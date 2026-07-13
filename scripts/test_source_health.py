#!/usr/bin/env python3
"""Deterministic tests for governed FREE-DOM source-health behavior."""
from __future__ import annotations

import pathlib
import tempfile

from source_health import (
    build_source_health,
    classify_source_failure,
    deduplicate_source_failures,
    persist_source_health_receipt,
    unique_source_urls,
)


def main() -> int:
    rows = [
        {"type": "rss", "url": "https://example.test/feed"},
        {"type": "rss", "url": "https://example.test/feed"},
        {"type": "site", "url": "https://example.test/"},
    ]
    assert unique_source_urls(rows, "rss") == ["https://example.test/feed"]
    assert unique_source_urls(rows, "site") == ["https://example.test/"]

    assert classify_source_failure("rss-fetch", "status=404") == "permanent"
    assert classify_source_failure("rss-fetch", "status=401") == "access-restricted"
    assert classify_source_failure("rss-parse", "not well-formed") == "malformed"
    assert classify_source_failure("rss-fetch", "TimeoutError") == "transient"
    assert classify_source_failure("site-fetch", "status=202") == "unexpected-response"

    failures = [
        {"source": "https://a.test/feed", "stage": "rss-fetch", "error": "status=404"},
        {"source": "https://a.test/feed", "stage": "rss-fetch", "error": "status=404"},
        {"source": "https://b.test/feed", "stage": "rss-fetch", "error": "status=401"},
    ]
    summarized = deduplicate_source_failures(failures)
    assert len(summarized) == 2
    assert summarized[0]["occurrence_count"] == 2

    receipt = build_source_health(
        run_id="TEST-RUN",
        configured_sources=["https://a.test/feed", "https://b.test/feed", "https://c.test/feed"],
        failures=failures,
        minimum_healthy_coverage=0.30,
    )
    assert receipt["result"] == "PASS"
    assert receipt["healthy_source_count"] == 1
    assert receipt["failed_source_count"] == 2
    assert receipt["authority"]["canonical_write"] is False
    assert receipt["authority"]["promotion"] is False

    with tempfile.TemporaryDirectory() as temp_dir:
        path, persisted = persist_source_health_receipt(
            base=pathlib.Path(temp_dir),
            run_id="TEST-RUN",
            configured_sources=["https://a.test/feed"],
            failures=[],
        )
        assert path.exists()
        assert persisted["result"] == "PASS"
        assert persisted["healthy_coverage"] == 1.0

    print("PASS source health classification, deduplication, coverage, and authority tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
