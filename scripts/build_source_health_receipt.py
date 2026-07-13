#!/usr/bin/env python3
"""Build a governed source-health receipt from the newest FREE-DOM run artifact."""
from __future__ import annotations

import argparse
import csv
import json
import pathlib

from source_health import persist_source_health_receipt, unique_source_urls


def newest_run_artifact(root: pathlib.Path) -> pathlib.Path:
    candidates = sorted(root.glob("EVID-FREEDOM-RUN-*.json"), key=lambda path: path.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError(f"No search-run artifacts found under {root}")
    return candidates[-1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=".")
    parser.add_argument("--minimum-healthy-coverage", type=float, default=0.50)
    args = parser.parse_args()

    base = pathlib.Path(args.base).resolve()
    artifact_path = newest_run_artifact(base / "data" / "evidence" / "artifacts")
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    run_id = str(artifact.get("run_id") or artifact_path.stem)
    failures = artifact.get("results", {}).get("source_failures", [])
    if not isinstance(failures, list):
        raise ValueError("search-run artifact results.source_failures must be a list")

    whitelist_path = base / "data" / "sources" / "sources_whitelist.csv"
    with whitelist_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    configured_sources = unique_source_urls(rows, "rss") + unique_source_urls(rows, "site")

    path, receipt = persist_source_health_receipt(
        base=base,
        run_id=run_id,
        configured_sources=configured_sources,
        failures=failures,
        minimum_healthy_coverage=args.minimum_healthy_coverage,
    )
    print(
        f"{receipt['result']} source_health={path.relative_to(base).as_posix()} "
        f"healthy={receipt['healthy_source_count']}/{receipt['configured_source_count']} "
        f"unique_failures={len(receipt['failures'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
