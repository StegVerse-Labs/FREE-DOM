#!/usr/bin/env python3
"""Deterministic regression test for canonical read-only search-agent behavior."""
from __future__ import annotations

import hashlib
import json
import pathlib
import tempfile

import pandas as pd

import search_agent


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    with tempfile.TemporaryDirectory() as temp_dir:
        base = pathlib.Path(temp_dir)
        master_dir = base / "data" / "master"
        source_dir = base / "data" / "sources"
        master_dir.mkdir(parents=True)
        source_dir.mkdir(parents=True)

        master_path = master_dir / "master_timeline.csv"
        people_path = master_dir / "verified_people_events.csv"
        whitelist_path = source_dir / "sources_whitelist.csv"

        pd.DataFrame(
            [
                {
                    "date": "2026-01-01",
                    "location": "Test Location",
                    "event": "Test Event",
                    "participants_on_record": "",
                    "source_urls": "",
                    "notes": "canonical note",
                    "deep_search_event": "pending",
                    "deep_search_notes": "",
                }
            ]
        ).to_csv(master_path, index=False)

        pd.DataFrame(
            [
                {
                    "date": "2026-01-01",
                    "location": "Test Location",
                    "event": "Test Event",
                    "person": "Test Person",
                    "role": "",
                    "source_urls": "",
                    "deep_search_person": "pending",
                    "deep_search_notes": "canonical person note",
                }
            ]
        ).to_csv(people_path, index=False)

        whitelist_path.write_text("type,url\n", encoding="utf-8")
        before = {master_path: digest(master_path), people_path: digest(people_path)}

        original_argv = list(__import__("sys").argv)
        try:
            __import__("sys").argv = [
                "search_agent.py",
                "--base",
                str(base),
                "--max-event-targets",
                "1",
                "--max-person-targets",
                "1",
            ]
            result = search_agent.main()
        finally:
            __import__("sys").argv = original_argv

        if result != 0:
            raise AssertionError(f"unexpected search-agent result: {result}")

        after = {master_path: digest(master_path), people_path: digest(people_path)}
        if before != after:
            raise AssertionError(
                "canonical input changed: "
                + json.dumps(
                    {
                        path.as_posix(): {"before": before[path], "after": after[path]}
                        for path in before
                    },
                    sort_keys=True,
                )
            )

        evidence_root = base / "data" / "evidence"
        if not evidence_root.exists():
            raise AssertionError("governed run evidence was not emitted")

    print("ALLOW search_agent_canonical_read_only_test_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
