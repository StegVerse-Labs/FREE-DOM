#!/usr/bin/env python3
"""Emit reconstructable evidence that a bounded FREE-DOM search sweep executed.

A search-run receipt proves execution conditions and recorded results. Zero hits do
not prove absence, falsity, or completeness. Source failures remain explicit.
"""
from __future__ import annotations

import json
import os
import pathlib
from typing import Any

from evidence_chain import (
    MANIFEST_VERSION,
    POLICY_REF,
    RECEIPT_VERSION,
    canonical_bytes,
    safe_slug,
    sha256_value,
    utc_now,
)


def persist_search_run(
    *,
    base: pathlib.Path,
    run_id: str,
    started_at: str,
    completed_at: str | None,
    event_targets: int,
    person_targets: int,
    rss_sources: int,
    page_sources: int,
    total_hits: int,
    hit_receipts: int,
    failures: list[dict[str, Any]],
    log_path: pathlib.Path,
) -> dict[str, str]:
    completed_at = completed_at or utc_now()
    artifact = {
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "scope": {
            "pending_event_targets": event_targets,
            "pending_person_targets": person_targets,
            "rss_sources": rss_sources,
            "page_sources": page_sources,
        },
        "results": {
            "total_hits": total_hits,
            "hit_receipts": hit_receipts,
            "source_failures": failures,
        },
        "limitations": [
            "zero hits do not prove absence",
            "search coverage is limited to configured public sources and generated keywords",
            "source retrieval failures reduce observable coverage",
            "a run receipt grants no factual standing to any subject claim",
        ],
        "log_pointer": log_path.relative_to(base).as_posix(),
    }
    artifact_hash = sha256_value(artifact)
    evidence_id = "EVID-FREEDOM-RUN-" + artifact_hash.split(":", 1)[1][:24]
    claim_text = f"FREE-DOM public OSINT sweep {run_id} executed under recorded scope"
    claim_hash = sha256_value({"claim_text": claim_text})

    manifest: dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "evidence_id": evidence_id,
        "producer_node_id": "StegVerse-Labs/FREE-DOM",
        "created_at": completed_at,
        "artifact": {
            "media_type": "application/vnd.stegverse.search-run+json",
            "content_hash": artifact_hash,
            "size_bytes": len(canonical_bytes(artifact)),
            "source_pointer": artifact["log_pointer"],
            "custody": "producer-local",
        },
        "provenance": {
            "origin_type": "derived-artifact",
            "origin_pointer": artifact["log_pointer"],
            "publisher_or_issuer": "StegVerse-Labs/FREE-DOM",
            "author_or_actor": "github-actions:FREE-DOM-ai-search-agent",
            "published_at": None,
            "event_time_start": started_at,
            "event_time_end": completed_at,
            "captured_at": completed_at,
            "discovery_method": "FREE-DOM bounded public OSINT sweep",
            "discovery_run_id": run_id,
            "executed_commit": os.environ.get("GITHUB_SHA") or None,
        },
        "subjects": [{
            "subject_id": f"artifact:search-run:{safe_slug(run_id, 48)}",
            "subject_type": "artifact",
            "display_name": f"FREE-DOM search run {run_id}",
            "identity_posture": "public-confirmed",
        }],
        "claims": [{
            "claim_id": "CLAIM-RUN-EXECUTED-" + claim_hash.split(":", 1)[1][:24],
            "claim_role": "observes",
            "claim_text": claim_text,
            "claim_text_hash": claim_hash,
            "scope": "Execution and recorded result only; no absence or truth inference.",
        }],
        "source_posture": "primary",
        "privacy_posture": {
            "classification": "public",
            "public_derivative_allowed": True,
            "redactions_required": [],
        },
        "supersedes_manifest_id": None,
        "manifest_hash": "",
    }
    manifest["manifest_hash"] = sha256_value({k: v for k, v in manifest.items() if k != "manifest_hash"})

    reason_codes = ["search-run-executed", "results-bounded-by-configured-scope"]
    if total_hits == 0:
        reason_codes.append("zero-hits-not-absence-proof")
    if failures:
        reason_codes.append("source-coverage-degraded")

    receipt: dict[str, Any] = {
        "receipt_version": RECEIPT_VERSION,
        "receipt_id": "RCPT-RUN-" + evidence_id.split("-")[-1],
        "evidence_id": evidence_id,
        "manifest_hash": manifest["manifest_hash"],
        "producer_node_id": "StegVerse-Labs/FREE-DOM",
        "actor": "github-actions:FREE-DOM-ai-search-agent",
        "authority_class": "observe",
        "transition_type": "captured",
        "occurred_at": completed_at,
        "effective_at": completed_at,
        "policy_ref": POLICY_REF,
        "input_state": "search-run-started",
        "output_state": "search-run-recorded",
        "result": "WARN" if failures else "RECORDED",
        "reason_codes": reason_codes,
        "evidence_effect": "discovery-only",
        "standing": {
            "status": "unreviewed",
            "as_of": completed_at,
            "basis_receipt_ids": [],
            "counterevidence_receipt_ids": [],
            "unresolved_questions": [
                "Whether additional sources or alternate queries would produce different results."
            ],
            "excluded_inferences": [
                "absence of an event, person, relationship, or record",
                "completeness of public-source coverage",
                "truth or falsity of any subject claim",
                "culpability or exoneration",
            ],
        },
        "acknowledgment": {
            "destination_node_id": "StegVerse-Labs/Executive_Rhetoric_Ledger",
            "status": "pending",
            "acknowledgment_id": None,
        },
        "previous_receipt_hash": None,
        "supersedes_receipt_id": None,
        "receipt_hash": "",
        "signature": None,
    }
    receipt["receipt_hash"] = sha256_value({k: v for k, v in receipt.items() if k != "receipt_hash"})

    root = base / "data" / "evidence"
    artifact_path = root / "artifacts" / f"{evidence_id}.json"
    manifest_path = root / "manifests" / f"{evidence_id}.json"
    receipt_path = root / "receipts" / f"{receipt['receipt_id']}.json"
    for path in (artifact_path, manifest_path, receipt_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "evidence_id": evidence_id,
        "manifest_path": manifest_path.relative_to(base).as_posix(),
        "manifest_hash": manifest["manifest_hash"],
        "receipt_path": receipt_path.relative_to(base).as_posix(),
        "receipt_id": receipt["receipt_id"],
        "receipt_hash": receipt["receipt_hash"],
    }
