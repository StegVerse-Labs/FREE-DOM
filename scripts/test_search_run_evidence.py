#!/usr/bin/env python3
"""Deterministic smoke test for a zero-hit FREE-DOM search-run evidence chain."""
from __future__ import annotations

import json
import pathlib
import tempfile

from evidence_chain import write_run_merkle_batch
from search_run_evidence import persist_search_run
from validate_evidence_outputs import validate


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        base = pathlib.Path(temp)
        log_path = base / "data" / "logs" / "ai_agent" / "agent_run_TEST.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps({"type": "test-run-start"}) + "\n", encoding="utf-8")

        ref = persist_search_run(
            base=base,
            run_id="TEST-ZERO-HIT-001",
            started_at="2026-07-12T00:00:00Z",
            completed_at="2026-07-12T00:00:01Z",
            event_targets=2,
            person_targets=1,
            rss_sources=3,
            page_sources=2,
            total_hits=0,
            hit_receipts=0,
            failures=[{
                "source": "https://example.invalid/feed",
                "stage": "rss-parse",
                "error": "synthetic test failure",
            }],
            log_path=log_path,
        )
        batch = write_run_merkle_batch(base, "TEST-ZERO-HIT-001", [ref])
        if batch is None:
            raise AssertionError("run receipt did not produce a Merkle batch")

        counts = validate(base)
        if counts != (1, 1, 1, 1):
            raise AssertionError(f"unexpected validation counts: {counts}")

        receipt = json.loads((base / ref["receipt_path"]).read_text(encoding="utf-8"))
        reasons = receipt.get("reason_codes", [])
        excluded = (receipt.get("standing") or {}).get("excluded_inferences", [])
        if "zero-hits-not-absence-proof" not in reasons:
            raise AssertionError("zero-hit safeguard reason is missing")
        if not any("absence" in str(value).lower() for value in excluded):
            raise AssertionError("absence inference is not explicitly excluded")

    print("ALLOW zero_hit_search_run_evidence_test_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
