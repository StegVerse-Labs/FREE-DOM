#!/usr/bin/env python3
"""Deterministic governance test for scripts/import_pending.py."""
from __future__ import annotations

import csv
import pathlib
import subprocess
import sys
import tempfile


def write_csv(path: pathlib.Path, header: list[str], row: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerow(row)


def main() -> int:
    repo = pathlib.Path(__file__).resolve().parents[1]
    importer = repo / "scripts" / "import_pending.py"

    with tempfile.TemporaryDirectory() as temp_dir:
        base = pathlib.Path(temp_dir)
        pending = base / "data" / "pending"
        header = [
            "date",
            "location",
            "event",
            "participants_on_record",
            "source_urls",
            "notes",
            "deep_search_event",
            "deep_search_notes",
        ]
        write_csv(
            pending / "pending_updates_template.csv",
            header,
            ["2026-01-01", "Example", "Template only", "Nobody", "https://example.invalid", "template", "pending", ""],
        )
        write_csv(
            pending / "pending_updates_batch001.csv",
            header,
            ["2026-01-02", "Example", "Real pending batch", "Nobody", "https://example.invalid", "pending", "pending", ""],
        )

        result = subprocess.run(
            [sys.executable, str(importer), "--base", str(base)],
            check=True,
            capture_output=True,
            text=True,
        )
        output = result.stdout
        if "Validated 1 non-template pending batch(es)." not in output:
            raise AssertionError(output)
        if "DENY promotion_authority_missing" not in output:
            raise AssertionError(output)
        if (base / "data" / "master" / "master_timeline.csv").exists():
            raise AssertionError("default validation mutated canonical records")
        if not (pending / "pending_updates_template.csv").exists():
            raise AssertionError("template input was moved or deleted")
        if not (pending / "pending_updates_batch001.csv").exists():
            raise AssertionError("pending input was moved without promotion authority")

    print("ALLOW import_pending_governance_test_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
