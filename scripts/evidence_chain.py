#!/usr/bin/env python3
"""Portable StegVerse evidence-chain production helpers.

This module emits canonical FREE-DOM discovery evidence using the shared
StegVerse-Labs/repo-standards ST-007 v1 contracts. A discovery artifact proves
what the search node observed and recorded. It does not claim custody of, or
truth for, the underlying linked source.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

MANIFEST_VERSION = "stegverse.evidence-manifest.v1"
RECEIPT_VERSION = "stegverse.evidence-transition-receipt.v1"
BATCH_VERSION = "stegverse.evidence-merkle-batch.v1"
POLICY_REF = "StegVerse-Labs/repo-standards:ST-007@v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_value(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def safe_slug(value: str, limit: int = 72) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return (slug or "unknown")[:limit]


def classify_origin(link: str) -> str:
    host = urlparse(link).netloc.lower()
    if any(token in host for token in ("courtlistener", "uscourts", "supremecourt")):
        return "court-record"
    if host.endswith(".gov") or ".gov." in host or "house.gov" in host or "senate.gov" in host:
        return "official-record"
    return "secondary-report"


def identity_posture(subject_type: str, display_name: str | None) -> str:
    if subject_type == "person" and not display_name:
        return "unresolved"
    return "public-disputed"


def make_manifest(
    *,
    hit: dict[str, Any],
    target_type: str,
    target_label: str,
    target_row_key: str,
    keywords: list[str],
    captured_at: str,
    run_id: str,
    executed_commit: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    link = str(hit.get("link") or "").strip()
    title = str(hit.get("title") or "").strip()
    published = str(hit.get("published") or "").strip() or None
    discovery_artifact = {
        "target_type": target_type,
        "target_label": target_label,
        "target_row_key": target_row_key,
        "keywords": keywords,
        "hit": hit,
        "captured_at": captured_at,
        "run_id": run_id,
    }
    artifact_hash = sha256_value(discovery_artifact)
    evidence_id = "EVID-FREEDOM-" + artifact_hash.split(":", 1)[1][:24]
    claim_text = title or f"Discovery hit for {target_label}"
    claim_hash = sha256_value({"claim_text": claim_text})

    manifest: dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "evidence_id": evidence_id,
        "producer_node_id": "StegVerse-Labs/FREE-DOM",
        "created_at": captured_at,
        "artifact": {
            "media_type": "application/vnd.stegverse.discovery-record+json",
            "content_hash": artifact_hash,
            "size_bytes": len(canonical_bytes(discovery_artifact)),
            "source_pointer": link,
            "custody": "external-pointer",
        },
        "provenance": {
            "origin_type": classify_origin(link),
            "origin_pointer": link,
            "publisher_or_issuer": urlparse(link).netloc or None,
            "author_or_actor": None,
            "published_at": None,
            "event_time_start": None,
            "event_time_end": None,
            "captured_at": captured_at,
            "discovery_method": "FREE-DOM public OSINT whitelist keyword sweep",
            "discovery_run_id": run_id,
            "executed_commit": executed_commit,
        },
        "subjects": [
            {
                "subject_id": f"{target_type}:{safe_slug(target_label)}",
                "subject_type": target_type,
                "display_name": target_label or None,
                "identity_posture": identity_posture(target_type, target_label or None),
            }
        ],
        "claims": [
            {
                "claim_id": "CLAIM-DISCOVERY-" + claim_hash.split(":", 1)[1][:24],
                "claim_role": "observes",
                "claim_text": claim_text,
                "claim_text_hash": claim_hash,
                "scope": "Discovery only; linked content remains unreviewed.",
            }
        ],
        "source_posture": "unreviewed",
        "privacy_posture": {
            "classification": "public-with-review",
            "public_derivative_allowed": True,
            "redactions_required": [],
        },
        "supersedes_manifest_id": None,
        "manifest_hash": "",
    }
    manifest["manifest_hash"] = sha256_value({k: v for k, v in manifest.items() if k != "manifest_hash"})
    return manifest, discovery_artifact


def make_discovery_receipt(manifest: dict[str, Any], occurred_at: str) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "receipt_version": RECEIPT_VERSION,
        "receipt_id": "RCPT-DISCOVERED-" + manifest["evidence_id"].split("-")[-1],
        "evidence_id": manifest["evidence_id"],
        "manifest_hash": manifest["manifest_hash"],
        "producer_node_id": "StegVerse-Labs/FREE-DOM",
        "actor": {
            "actor_id": "github-actions:FREE-DOM-ai-search-agent",
            "authority_class": "discovery-only",
        },
        "transition_type": "discovered",
        "occurred_at": occurred_at,
        "policy_ref": POLICY_REF,
        "input_state": "not-recorded",
        "output_state": "discovered-unreviewed",
        "result": "ALLOW",
        "evidence_effect": "none-until-governed-review",
        "current_standing": "unreviewed",
        "counterevidence_refs": [],
        "excluded_inferences": [
            "underlying claim truth",
            "identity confirmation beyond target label",
            "association culpability",
            "victim contact",
            "criminal knowledge or participation",
        ],
        "acknowledgment": {
            "required": True,
            "status": "pending",
            "consumer": None,
        },
        "previous_receipt_hash": None,
        "supersedes_receipt_id": None,
        "receipt_hash": "",
    }
    receipt["receipt_hash"] = sha256_value({k: v for k, v in receipt.items() if k != "receipt_hash"})
    return receipt


def calculate_merkle_root(hashes: list[str]) -> str:
    if not hashes:
        raise ValueError("Merkle batch requires at least one receipt hash")
    level = [bytes.fromhex(value.split(":", 1)[1]) for value in hashes]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [
            hashlib.sha256(level[index] + level[index + 1]).digest()
            for index in range(0, len(level), 2)
        ]
    return "sha256:" + level[0].hex()


def persist_discovery(
    *,
    base: pathlib.Path,
    hit: dict[str, Any],
    target_type: str,
    target_label: str,
    target_row_key: str,
    keywords: list[str],
    run_id: str,
    captured_at: str | None = None,
) -> dict[str, str]:
    captured_at = captured_at or utc_now()
    executed_commit = os.environ.get("GITHUB_SHA") or None
    manifest, artifact = make_manifest(
        hit=hit,
        target_type=target_type,
        target_label=target_label,
        target_row_key=target_row_key,
        keywords=keywords,
        captured_at=captured_at,
        run_id=run_id,
        executed_commit=executed_commit,
    )
    receipt = make_discovery_receipt(manifest, captured_at)

    root = base / "data" / "evidence"
    artifact_path = root / "artifacts" / f"{manifest['evidence_id']}.json"
    manifest_path = root / "manifests" / f"{manifest['evidence_id']}.json"
    receipt_path = root / "receipts" / f"{receipt['receipt_id']}.json"
    for path in (artifact_path, manifest_path, receipt_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    artifact_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "evidence_id": manifest["evidence_id"],
        "manifest_path": manifest_path.relative_to(base).as_posix(),
        "manifest_hash": manifest["manifest_hash"],
        "receipt_path": receipt_path.relative_to(base).as_posix(),
        "receipt_id": receipt["receipt_id"],
        "receipt_hash": receipt["receipt_hash"],
    }


def write_run_merkle_batch(base: pathlib.Path, run_id: str, receipt_refs: list[dict[str, str]]) -> pathlib.Path | None:
    if not receipt_refs:
        return None
    ordered = sorted(receipt_refs, key=lambda item: item["receipt_id"])
    leaves = [item["receipt_hash"] for item in ordered]
    created_at = utc_now()
    batch: dict[str, Any] = {
        "batch_version": BATCH_VERSION,
        "batch_id": f"BATCH-FREEDOM-{safe_slug(run_id, 48)}",
        "producer_node_id": "StegVerse-Labs/FREE-DOM",
        "created_at": created_at,
        "hash_algorithm": "sha256",
        "leaf_receipt_hashes": leaves,
        "merkle_root": calculate_merkle_root(leaves),
        "previous_batch_hash": None,
        "checkpoint_ref": None,
        "signature": None,
        "batch_hash": "",
    }
    batch["batch_hash"] = sha256_value({k: v for k, v in batch.items() if k != "batch_hash"})
    path = base / "data" / "evidence" / "merkle" / f"{safe_slug(run_id, 64)}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
