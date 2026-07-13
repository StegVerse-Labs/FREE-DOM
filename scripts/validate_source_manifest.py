#!/usr/bin/env python3
"""Validate the governed FREE-DOM source lifecycle manifest.

The active whitelist is an execution projection of the manifest. Stable source IDs,
not mutable display labels, define source identity. The validator prevents duplicate
active URLs, silent source removal, guessed replacement URLs, and activation without
an authority/evidence trail.
"""
from __future__ import annotations

import argparse
import csv
import pathlib
from collections import Counter

ALLOWED_STATUS = {"active", "quarantined_pending_revalidation", "retired"}
ALLOWED_REPLACEMENT = {"none", "replacement_required", "revalidation_required", "replaced"}
REQUIRED_MANIFEST_COLUMNS = {
    "source_id",
    "name",
    "type",
    "url",
    "status",
    "expected_media_type",
    "observed_failure_class",
    "evidence_ref",
    "replacement_status",
    "authority_ref",
    "notes",
}
REQUIRED_WHITELIST_COLUMNS = {"source_id", "name", "type", "url", "notes"}


def read_csv(path: pathlib.Path, required_columns: set[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Missing CSV header: {path}")
        missing = required_columns - set(reader.fieldnames)
        if missing:
            raise ValueError(f"{path.name} missing columns: {sorted(missing)}")
        return list(reader)


def normalize(value: str | None) -> str:
    return (value or "").strip()


def validate(base: pathlib.Path) -> list[str]:
    source_root = base / "data" / "sources"
    manifest = read_csv(source_root / "source_manifest.csv", REQUIRED_MANIFEST_COLUMNS)
    whitelist = read_csv(source_root / "sources_whitelist.csv", REQUIRED_WHITELIST_COLUMNS)
    errors: list[str] = []

    ids = [normalize(row.get("source_id")) for row in manifest]
    duplicate_ids = sorted(key for key, count in Counter(ids).items() if key and count > 1)
    if duplicate_ids:
        errors.append(f"duplicate source_id values: {duplicate_ids}")

    urls = [normalize(row.get("url")) for row in manifest]
    duplicate_urls = sorted(key for key, count in Counter(urls).items() if key and count > 1)
    if duplicate_urls:
        errors.append(f"duplicate manifest URLs: {duplicate_urls}")

    active_projection: set[tuple[str, str, str]] = set()
    for index, row in enumerate(manifest, start=2):
        source_id = normalize(row.get("source_id"))
        url = normalize(row.get("url"))
        source_type = normalize(row.get("type")).lower()
        status = normalize(row.get("status")).lower()
        replacement = normalize(row.get("replacement_status")).lower()
        evidence_ref = normalize(row.get("evidence_ref"))
        authority_ref = normalize(row.get("authority_ref"))
        expected_media_type = normalize(row.get("expected_media_type"))

        if not source_id or not url or source_type not in {"rss", "site"}:
            errors.append(f"line {index}: source_id, supported type, and URL are required")
        if status not in ALLOWED_STATUS:
            errors.append(f"line {index}: unsupported status {status!r}")
        if replacement not in ALLOWED_REPLACEMENT:
            errors.append(f"line {index}: unsupported replacement_status {replacement!r}")
        if not expected_media_type:
            errors.append(f"line {index}: expected_media_type is required")
        if not evidence_ref or not authority_ref:
            errors.append(f"line {index}: evidence_ref and authority_ref are required")
        if status == "active":
            if replacement not in {"none", "replaced"}:
                errors.append(f"line {index}: active source cannot require replacement")
            active_projection.add((source_id, source_type, url))
        elif replacement == "none":
            errors.append(f"line {index}: non-active source must declare replacement or revalidation posture")

    whitelist_ids = [normalize(row.get("source_id")) for row in whitelist]
    duplicate_whitelist_ids = sorted(
        key for key, count in Counter(whitelist_ids).items() if key and count > 1
    )
    if duplicate_whitelist_ids:
        errors.append(f"duplicate active whitelist source IDs: {duplicate_whitelist_ids}")

    whitelist_urls = [normalize(row.get("url")) for row in whitelist]
    duplicate_whitelist_urls = sorted(
        key for key, count in Counter(whitelist_urls).items() if key and count > 1
    )
    if duplicate_whitelist_urls:
        errors.append(f"duplicate active whitelist URLs: {duplicate_whitelist_urls}")

    whitelist_projection = {
        (
            normalize(row.get("source_id")),
            normalize(row.get("type")).lower(),
            normalize(row.get("url")),
        )
        for row in whitelist
        if normalize(row.get("url"))
    }

    for index, row in enumerate(whitelist, start=2):
        if not normalize(row.get("source_id")):
            errors.append(f"whitelist line {index}: source_id is required")
        if normalize(row.get("type")).lower() not in {"rss", "site"}:
            errors.append(f"whitelist line {index}: supported type is required")

    missing_from_whitelist = sorted(active_projection - whitelist_projection)
    undeclared_active = sorted(whitelist_projection - active_projection)
    if missing_from_whitelist:
        errors.append(f"active manifest sources missing from whitelist: {missing_from_whitelist}")
    if undeclared_active:
        errors.append(f"whitelist sources not active in manifest: {undeclared_active}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=".")
    args = parser.parse_args()
    errors = validate(pathlib.Path(args.base).resolve())
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print("PASS governed source manifest matches active execution whitelist by source_id")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
