#!/usr/bin/env python3
"""Regression tests for governed source manifest projection rules."""
from __future__ import annotations

import csv
import pathlib
import tempfile

from validate_source_manifest import validate

MANIFEST_FIELDS = [
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
]
WHITELIST_FIELDS = ["name", "type", "url", "notes"]


def write_csv(path: pathlib.Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def base_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    manifest = [
        {
            "source_id": "SRC-A",
            "name": "Active A",
            "type": "rss",
            "url": "https://example.test/a.xml",
            "status": "active",
            "expected_media_type": "application/rss+xml",
            "observed_failure_class": "",
            "evidence_ref": "data/evidence/runs/example.json",
            "replacement_status": "none",
            "authority_ref": "FREE_DOM_MIRROR_HANDOFF.md",
            "notes": "active",
        },
        {
            "source_id": "SRC-B",
            "name": "Quarantined B",
            "type": "site",
            "url": "https://example.test/b",
            "status": "quarantined_pending_revalidation",
            "expected_media_type": "text/html",
            "observed_failure_class": "permanent",
            "evidence_ref": "data/evidence/runs/example.json",
            "replacement_status": "replacement_required",
            "authority_ref": "FREE_DOM_MIRROR_HANDOFF.md",
            "notes": "quarantined",
        },
    ]
    whitelist = [
        {
            "name": "Active A",
            "type": "rss",
            "url": "https://example.test/a.xml",
            "notes": "active projection",
        }
    ]
    return manifest, whitelist


def run_case(manifest: list[dict[str, str]], whitelist: list[dict[str, str]]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp)
        write_csv(base / "data/sources/source_manifest.csv", MANIFEST_FIELDS, manifest)
        write_csv(base / "data/sources/sources_whitelist.csv", WHITELIST_FIELDS, whitelist)
        return validate(base)


def main() -> int:
    manifest, whitelist = base_rows()
    assert run_case(manifest, whitelist) == []

    duplicate = [dict(row) for row in manifest]
    duplicate.append(dict(manifest[0], source_id="SRC-C"))
    assert any("duplicate manifest URLs" in error for error in run_case(duplicate, whitelist))

    undeclared = [dict(row) for row in whitelist]
    undeclared.append({"name": "Unknown", "type": "rss", "url": "https://example.test/u.xml", "notes": ""})
    assert any("not active in manifest" in error for error in run_case(manifest, undeclared))

    missing = []
    assert any("missing from whitelist" in error for error in run_case(manifest, missing))

    invalid = [dict(row) for row in manifest]
    invalid[1]["replacement_status"] = "none"
    assert any("non-active source" in error for error in run_case(invalid, whitelist))

    print("PASS governed source manifest regression tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
