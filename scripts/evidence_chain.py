#!/usr/bin/env python3
"""Portable StegVerse evidence-chain production helpers.

Emits canonical FREE-DOM discovery evidence using shared ST-007 v1 contracts.
A discovery artifact proves what the search node observed and recorded; it does
not establish truth of the linked source.
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
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


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


def make_manifest(*, hit: dict[str, Any], target_type: str, target_label: str,
                  target_row_key: str, keywords: list[str], captured_at: str,
                  run_id: str, executed_commit: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    link = str(hit.get("link") or "").strip()
    title = str(hit.get("title") or "").strip()
    artifact = {
        "target_type": target_type,
        "target_label": target_label,
        "target_row_key": target_row_key,
        "keywords": keywords,
        "hit": hit,
        "captured_at": captured_at,
        "run_id": run_id,
    }
    artifact_hash = sha256_value(artifact)
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
            "size_bytes": len(canonical_bytes(artifact)),
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
        "subjects": [{
            "subject_id": f"{target_type}:{safe_slug(target_label)}",
            "subject_type": target_type,
            "display_name": target_label or None,
            "identity_posture": identity_posture(target_type, target_label or None),
        }],
        "claims": [{
            "claim_id": "CLAIM-DISCOVERY-" + claim_hash.split(":", 1)[1][:24],
            "claim_role": "observes",
            "claim_text": claim_text,
            "claim_text_hash": claim_hash,
            "scope": "Discovery only; linked content remains unreviewed.",
        }],
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
    return manifest, artifact


def make_discovery_receipt(manifest: dict[str, Any], occurred_at: str) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "receipt_version": RECEIPT_VERSION,
        "receipt_id": "RCPT-DISCOVERED-" + manifest["evidence_id"].split("-")[-1],
        "evidence_id": manifest["evidence_id"],
        "manifest_hash": manifest["manifest_hash"],
        "producer_node_id": "StegVerse-Labs/FREE-DOM",
        "actor": "github-actions:FREE-DOM-ai-search-agent",
        "authority_class": "observe",
        "transition_type": "discovered",
        "occurred_at": occurred_at,
        "effective_at": occurred_at,
        "policy_ref": POLICY_REF,
        "input_state": "not-recorded",
        "output_state": "discovered-unreviewed",
        "result": "RECORDED",
        "reason_codes": ["public-osint-hit", "governed-review-required"],
        "evidence_effect": "discovery-only",
        "standing": {
            "status": "unreviewed",
            "as_of": occurred_at,
            "basis_receipt_ids": [],
            "counterevidence_receipt_ids": [],
            "unresolved_questions": ["Whether the linked source supports any material claim."],
            "excluded_inferences": [
                "underlying claim truth", "identity confirmation beyond target label",
                "association culpability", "victim contact", "criminal knowledge or participation",
            ],
        },
        "acknowledgment": {
            "destination_node_id": "unassigned-governed-consumer",
            "status": "pending",
            "acknowledgment_id": None,
        },
        "previous_receipt_hash": None,
        "supersedes_receipt_id": None,
        "receipt_hash": "",
        "signature": None,
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
        level = [hashlib.sha256(level[i] + level[i + 1]).digest() for i in range(0, len(level), 2)]
    return "sha256:" + level[0].hex()


def merkle_proof(hashes: list[str], index: int) -> list[dict[str, str]]:
    level = [bytes.fromhex(value.split(":", 1)[1]) for value in hashes]
    position = index
    proof: list[dict[str, str]] = []
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        sibling = position - 1 if position % 2 else position + 1
        proof.append({
            "position": "left" if sibling < position else "right",
            "hash": "sha256:" + level[sibling].hex(),
        })
        level = [hashlib.sha256(level[i] + level[i + 1]).digest() for i in range(0, len(level), 2)]
        position //= 2
    return proof


def persist_discovery(*, base: pathlib.Path, hit: dict[str, Any], target_type: str,
                      target_label: str, target_row_key: str, keywords: list[str],
                      run_id: str, captured_at: str | None = None) -> dict[str, str]:
    captured_at = captured_at or utc_now()
    manifest, artifact = make_manifest(
        hit=hit, target_type=target_type, target_label=target_label,
        target_row_key=target_row_key, keywords=keywords, captured_at=captured_at,
        run_id=run_id, executed_commit=os.environ.get("GITHUB_SHA") or None,
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


def _latest_previous_batch(merkle_dir: pathlib.Path) -> tuple[str | None, str | None]:
    candidates: list[tuple[str, str, str]] = []
    for path in merkle_dir.glob("*.json") if merkle_dir.exists() else []:
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        created_at, batch_hash = obj.get("created_at"), obj.get("batch_hash")
        if isinstance(created_at, str) and isinstance(batch_hash, str):
            candidates.append((created_at, path.name, batch_hash))
    if not candidates:
        return None, None
    _, filename, batch_hash = sorted(candidates)[-1]
    return batch_hash, f"data/evidence/merkle/{filename}"


def write_run_merkle_batch(base: pathlib.Path, run_id: str,
                           receipt_refs: list[dict[str, str]]) -> pathlib.Path | None:
    if not receipt_refs:
        return None
    ordered = sorted(receipt_refs, key=lambda item: item["receipt_id"])
    leaves = [item["receipt_hash"] for item in ordered]
    created_at = utc_now()
    merkle_dir = base / "data" / "evidence" / "merkle"
    previous_hash, previous_ref = _latest_previous_batch(merkle_dir)
    batch: dict[str, Any] = {
        "batch_version": BATCH_VERSION,
        "batch_id": f"BATCH-FREEDOM-{safe_slug(run_id, 48)}",
        "producer_node_id": "StegVerse-Labs/FREE-DOM",
        "created_at": created_at,
        "hash_algorithm": "sha256",
        "leaf_order": "lexicographic-receipt-id",
        "leaf_receipt_hashes": leaves,
        "merkle_root": calculate_merkle_root(leaves),
        "previous_batch_hash": previous_hash,
        "checkpoint_ref": previous_ref,
        "batch_hash": "",
        "signature": None,
    }
    batch["batch_hash"] = sha256_value({k: v for k, v in batch.items() if k != "batch_hash"})
    merkle_dir.mkdir(parents=True, exist_ok=True)
    path = merkle_dir / f"{safe_slug(run_id, 64)}.json"
    path.write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    proofs_dir = base / "data" / "evidence" / "proofs" / safe_slug(run_id, 64)
    proofs_dir.mkdir(parents=True, exist_ok=True)
    for index, ref in enumerate(ordered):
        proof = {
            "proof_version": "stegverse.merkle-inclusion-proof.v1",
            "batch_id": batch["batch_id"],
            "batch_hash": batch["batch_hash"],
            "merkle_root": batch["merkle_root"],
            "receipt_id": ref["receipt_id"],
            "receipt_hash": ref["receipt_hash"],
            "leaf_index": index,
            "siblings": merkle_proof(leaves, index),
        }
        proof["proof_hash"] = sha256_value(proof)
        proof_path = proofs_dir / f"{safe_slug(ref['receipt_id'], 96)}.json"
        proof_path.write_text(json.dumps(proof, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
