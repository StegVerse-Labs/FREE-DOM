#!/usr/bin/env python3
"""Governed source-health utilities for FREE-DOM public-source sweeps.

Source health describes retrieval coverage only. It grants no factual standing to
search results and never authorizes canonical writes or record promotion.
"""
from __future__ import annotations

import json
import pathlib
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

SOURCE_HEALTH_SCHEMA = "stegverse.free-dom.source-health.v1"
DEFAULT_MINIMUM_HEALTHY_COVERAGE = 0.50


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def unique_source_urls(rows: Iterable[dict[str, str]], source_type: str) -> list[str]:
    """Return stable, unique configured URLs for one source type."""
    output: list[str] = []
    seen: set[str] = set()
    wanted = source_type.strip().lower()
    for row in rows:
        url = (row.get("url") or "").strip()
        row_type = (row.get("type") or "rss").strip().lower()
        if not url or row_type != wanted or url in seen:
            continue
        seen.add(url)
        output.append(url)
    return output


def classify_source_failure(stage: str, error: str) -> str:
    """Classify a retrieval failure without inferring source intent."""
    text = f"{stage} {error}".lower()
    status_match = re.search(r"status=(\d{3})", text)
    status = int(status_match.group(1)) if status_match else None

    if status in {404, 410}:
        return "permanent"
    if status in {401, 403}:
        return "access-restricted"
    if "parse" in text or "malformed" in text or "not well-formed" in text:
        return "malformed"
    if status == 429 or (status is not None and status >= 500):
        return "transient"
    if any(token in text for token in ("timeout", "connection", "temporar", "dns", "name resolution")):
        return "transient"
    if status is not None and status != 200:
        return "unexpected-response"
    return "unknown"


def deduplicate_source_failures(failures: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse repeated failures and retain their observed occurrence count."""
    grouped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for failure in failures:
        source = str(failure.get("source", "")).strip()
        stage = str(failure.get("stage", "unknown")).strip() or "unknown"
        error = str(failure.get("error", "unknown error")).strip() or "unknown error"
        classification = classify_source_failure(stage, error)
        key = (source, stage, classification, error)
        if key not in grouped:
            grouped[key] = {
                "source": source,
                "stage": stage,
                "classification": classification,
                "error": error,
                "occurrence_count": 0,
            }
        grouped[key]["occurrence_count"] += 1
    return sorted(grouped.values(), key=lambda item: (item["source"], item["stage"], item["error"]))


def build_source_health(
    *,
    run_id: str,
    configured_sources: Iterable[str],
    failures: Iterable[dict[str, Any]],
    minimum_healthy_coverage: float = DEFAULT_MINIMUM_HEALTHY_COVERAGE,
) -> dict[str, Any]:
    configured = list(dict.fromkeys(str(url).strip() for url in configured_sources if str(url).strip()))
    summarized_failures = deduplicate_source_failures(failures)
    failed_sources = sorted({item["source"] for item in summarized_failures if item["source"]})
    healthy_sources = [url for url in configured if url not in failed_sources]
    configured_count = len(configured)
    healthy_count = len(healthy_sources)
    coverage = healthy_count / configured_count if configured_count else 0.0
    classifications = Counter(item["classification"] for item in summarized_failures)

    return {
        "schema": SOURCE_HEALTH_SCHEMA,
        "run_id": run_id,
        "generated_at": utc_now(),
        "result": "PASS" if configured_count and coverage >= minimum_healthy_coverage else "WARN",
        "minimum_healthy_coverage": minimum_healthy_coverage,
        "healthy_coverage": round(coverage, 6),
        "configured_source_count": configured_count,
        "healthy_source_count": healthy_count,
        "failed_source_count": len(failed_sources),
        "configured_sources": configured,
        "healthy_sources": healthy_sources,
        "failed_sources": failed_sources,
        "failure_classification_counts": dict(sorted(classifications.items())),
        "failures": summarized_failures,
        "authority": {
            "canonical_write": False,
            "promotion": False,
            "source_manifest_mutation": False,
        },
        "limitations": [
            "source health measures retrieval coverage, not factual truth",
            "a healthy response does not establish completeness or correctness",
            "a failed response does not establish source unavailability outside this run",
            "zero search hits remain a valid bounded outcome",
        ],
    }


def persist_source_health_receipt(
    *,
    base: pathlib.Path,
    run_id: str,
    configured_sources: Iterable[str],
    failures: Iterable[dict[str, Any]],
    minimum_healthy_coverage: float = DEFAULT_MINIMUM_HEALTHY_COVERAGE,
) -> tuple[pathlib.Path, dict[str, Any]]:
    receipt = build_source_health(
        run_id=run_id,
        configured_sources=configured_sources,
        failures=failures,
        minimum_healthy_coverage=minimum_healthy_coverage,
    )
    path = base / "data" / "evidence" / "source-health" / f"source-health-{run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path, receipt
