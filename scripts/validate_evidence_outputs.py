#!/usr/bin/env python3
"""Fail-closed validation for FREE-DOM ST-007 evidence outputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
from typing import Any

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def load(path: pathlib.Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be an object")
    return data


def canonical_hash(obj: dict[str, Any], hash_field: str) -> str:
    payload = {k: v for k, v in obj.items() if k != hash_field}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def require_hash(value: Any, label: str, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{label}: invalid sha256 value")


def calculate_merkle_root(hashes: list[str]) -> str:
    if not hashes:
        raise ValueError("Merkle batch has no leaves")
    level = [bytes.fromhex(v.split(":", 1)[1]) for v in hashes]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [hashlib.sha256(level[i] + level[i + 1]).digest() for i in range(0, len(level), 2)]
    return "sha256:" + level[0].hex()


def apply_proof(receipt_hash: str, siblings: list[dict[str, str]]) -> str:
    current = bytes.fromhex(receipt_hash.split(":", 1)[1])
    for step in siblings:
        sibling_hash = step.get("hash")
        require_hash(sibling_hash, "proof sibling")
        sibling = bytes.fromhex(sibling_hash.split(":", 1)[1])
        position = step.get("position")
        if position == "left":
            current = hashlib.sha256(sibling + current).digest()
        elif position == "right":
            current = hashlib.sha256(current + sibling).digest()
        else:
            raise ValueError("proof sibling position must be left or right")
    return "sha256:" + current.hex()


def validate(base: pathlib.Path) -> tuple[int, int, int, int]:
    root = base / "data" / "evidence"
    manifests_dir, receipts_dir = root / "manifests", root / "receipts"
    batches_dir, proofs_dir = root / "merkle", root / "proofs"
    manifests: dict[str, dict[str, Any]] = {}
    receipts: dict[str, dict[str, Any]] = {}

    for path in sorted(manifests_dir.glob("*.json")) if manifests_dir.exists() else []:
        obj = load(path)
        if obj.get("manifest_version") != "stegverse.evidence-manifest.v1":
            raise ValueError(f"{path}: unsupported manifest_version")
        if obj.get("manifest_hash") != canonical_hash(obj, "manifest_hash"):
            raise ValueError(f"{path}: manifest_hash mismatch")
        require_hash(obj.get("artifact", {}).get("content_hash"), f"{path}: artifact.content_hash")
        evidence_id = obj.get("evidence_id")
        if not evidence_id or evidence_id in manifests:
            raise ValueError(f"{path}: missing or duplicate evidence_id")
        manifests[evidence_id] = obj

    for path in sorted(receipts_dir.glob("*.json")) if receipts_dir.exists() else []:
        obj = load(path)
        if obj.get("receipt_version") != "stegverse.evidence-transition-receipt.v1":
            raise ValueError(f"{path}: unsupported receipt_version")
        if obj.get("receipt_hash") != canonical_hash(obj, "receipt_hash"):
            raise ValueError(f"{path}: receipt_hash mismatch")
        receipt_hash = obj.get("receipt_hash")
        require_hash(receipt_hash, f"{path}: receipt_hash")
        if receipt_hash in receipts:
            raise ValueError(f"{path}: duplicate receipt_hash")
        manifest = manifests.get(obj.get("evidence_id"))
        if manifest is None or obj.get("manifest_hash") != manifest.get("manifest_hash"):
            raise ValueError(f"{path}: receipt manifest binding invalid")
        if obj.get("authority_class") != "observe" or obj.get("evidence_effect") != "discovery-only":
            raise ValueError(f"{path}: FREE-DOM discovery receipt exceeds authority")
        receipts[receipt_hash] = obj

    batches: list[tuple[pathlib.Path, dict[str, Any]]] = []
    for path in sorted(batches_dir.glob("*.json")) if batches_dir.exists() else []:
        obj = load(path)
        if obj.get("batch_version") != "stegverse.evidence-merkle-batch.v1":
            raise ValueError(f"{path}: unsupported batch_version")
        if obj.get("leaf_order") != "lexicographic-receipt-id":
            raise ValueError(f"{path}: invalid leaf order")
        if obj.get("batch_hash") != canonical_hash(obj, "batch_hash"):
            raise ValueError(f"{path}: batch_hash mismatch")
        leaves = obj.get("leaf_receipt_hashes")
        if not isinstance(leaves, list) or not leaves or len(leaves) != len(set(leaves)):
            raise ValueError(f"{path}: invalid Merkle leaves")
        for leaf in leaves:
            require_hash(leaf, f"{path}: leaf")
            if leaf not in receipts:
                raise ValueError(f"{path}: unknown receipt leaf {leaf}")
        if obj.get("merkle_root") != calculate_merkle_root(leaves):
            raise ValueError(f"{path}: Merkle root mismatch")
        require_hash(obj.get("previous_batch_hash"), f"{path}: previous_batch_hash", nullable=True)
        batches.append((path, obj))

    ordered_batches = sorted(batches, key=lambda item: (item[1].get("created_at", ""), item[0].name))
    for index, (path, obj) in enumerate(ordered_batches):
        expected_previous = None if index == 0 else ordered_batches[index - 1][1].get("batch_hash")
        if obj.get("previous_batch_hash") != expected_previous:
            raise ValueError(f"{path}: previous_batch_hash does not match prior batch")

    proof_count = 0
    batch_by_id = {obj.get("batch_id"): obj for _, obj in batches}
    for path in sorted(proofs_dir.rglob("*.json")) if proofs_dir.exists() else []:
        proof = load(path)
        if proof.get("proof_version") != "stegverse.merkle-inclusion-proof.v1":
            raise ValueError(f"{path}: unsupported proof_version")
        if proof.get("proof_hash") != canonical_hash(proof, "proof_hash"):
            raise ValueError(f"{path}: proof_hash mismatch")
        batch = batch_by_id.get(proof.get("batch_id"))
        if batch is None or proof.get("batch_hash") != batch.get("batch_hash"):
            raise ValueError(f"{path}: proof batch binding invalid")
        receipt_hash = proof.get("receipt_hash")
        if receipt_hash not in receipts or receipt_hash not in batch.get("leaf_receipt_hashes", []):
            raise ValueError(f"{path}: proof receipt binding invalid")
        siblings = proof.get("siblings")
        if not isinstance(siblings, list) or apply_proof(receipt_hash, siblings) != batch.get("merkle_root"):
            raise ValueError(f"{path}: inclusion proof does not resolve to batch root")
        proof_count += 1

    expected_proofs = sum(len(obj.get("leaf_receipt_hashes", [])) for _, obj in batches)
    if proof_count != expected_proofs:
        raise ValueError(f"inclusion proof count mismatch: expected {expected_proofs}, found {proof_count}")
    return len(manifests), len(receipts), len(batches), proof_count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=".")
    args = parser.parse_args()
    try:
        counts = validate(pathlib.Path(args.base).resolve())
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"DENY evidence_outputs_invalid: {exc}", file=sys.stderr)
        return 1
    print(f"ALLOW evidence_outputs_valid manifests={counts[0]} receipts={counts[1]} batches={counts[2]} proofs={counts[3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
