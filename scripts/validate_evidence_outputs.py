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
    payload = {key: value for key, value in obj.items() if key != hash_field}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def require_hash(value: Any, label: str) -> None:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{label}: invalid sha256 value")


def calculate_merkle_root(hashes: list[str]) -> str:
    level = [bytes.fromhex(value.split(":", 1)[1]) for value in hashes]
    if not level:
        raise ValueError("Merkle batch has no leaves")
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [hashlib.sha256(level[i] + level[i + 1]).digest() for i in range(0, len(level), 2)]
    return "sha256:" + level[0].hex()


def validate(base: pathlib.Path) -> tuple[int, int, int]:
    root = base / "data" / "evidence"
    manifests_dir = root / "manifests"
    receipts_dir = root / "receipts"
    batches_dir = root / "merkle"

    manifests: dict[str, dict[str, Any]] = {}
    receipts_by_hash: dict[str, dict[str, Any]] = {}

    for path in sorted(manifests_dir.glob("*.json")) if manifests_dir.exists() else []:
        obj = load(path)
        if obj.get("manifest_version") != "stegverse.evidence-manifest.v1":
            raise ValueError(f"{path}: unsupported manifest_version")
        expected = canonical_hash(obj, "manifest_hash")
        if obj.get("manifest_hash") != expected:
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
        expected = canonical_hash(obj, "receipt_hash")
        if obj.get("receipt_hash") != expected:
            raise ValueError(f"{path}: receipt_hash mismatch")
        receipt_hash = obj.get("receipt_hash")
        require_hash(receipt_hash, f"{path}: receipt_hash")
        if receipt_hash in receipts_by_hash:
            raise ValueError(f"{path}: duplicate receipt_hash")
        evidence_id = obj.get("evidence_id")
        manifest = manifests.get(evidence_id)
        if manifest is None:
            raise ValueError(f"{path}: no manifest for evidence_id {evidence_id}")
        if obj.get("manifest_hash") != manifest.get("manifest_hash"):
            raise ValueError(f"{path}: receipt does not bind to manifest hash")
        if obj.get("authority_class") != "observe" or obj.get("evidence_effect") != "discovery-only":
            raise ValueError(f"{path}: FREE-DOM discovery receipt exceeds discovery authority")
        receipts_by_hash[receipt_hash] = obj

    for path in sorted(batches_dir.glob("*.json")) if batches_dir.exists() else []:
        obj = load(path)
        if obj.get("batch_version") != "stegverse.evidence-merkle-batch.v1":
            raise ValueError(f"{path}: unsupported batch_version")
        if obj.get("leaf_order") != "lexicographic-receipt-id":
            raise ValueError(f"{path}: invalid leaf order")
        expected_hash = canonical_hash(obj, "batch_hash")
        if obj.get("batch_hash") != expected_hash:
            raise ValueError(f"{path}: batch_hash mismatch")
        leaves = obj.get("leaf_receipt_hashes")
        if not isinstance(leaves, list) or not leaves:
            raise ValueError(f"{path}: missing Merkle leaves")
        for leaf in leaves:
            require_hash(leaf, f"{path}: leaf")
            if leaf not in receipts_by_hash:
                raise ValueError(f"{path}: unknown receipt leaf {leaf}")
        if obj.get("merkle_root") != calculate_merkle_root(leaves):
            raise ValueError(f"{path}: Merkle root mismatch")

    return len(manifests), len(receipts_by_hash), len(list(batches_dir.glob("*.json"))) if batches_dir.exists() else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=".")
    args = parser.parse_args()
    try:
        counts = validate(pathlib.Path(args.base).resolve())
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"DENY evidence_outputs_invalid: {exc}", file=sys.stderr)
        return 1
    print(f"ALLOW evidence_outputs_valid manifests={counts[0]} receipts={counts[1]} batches={counts[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
