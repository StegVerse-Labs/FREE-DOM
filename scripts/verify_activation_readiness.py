#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "evidence" / "verification" / "activation-readiness.json"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str, checks: list[dict]) -> None:
    checks.append({"check": message, "passed": bool(condition)})
    if not condition:
        raise AssertionError(message)


def commit_add_block(text: str) -> str:
    match = re.search(r"\n\s*add:\s*\|(?P<body>.*?)(?:\n\s*[A-Za-z_][^\n]*:|\Z)", text, re.S)
    return match.group("body") if match else ""


def main() -> int:
    checks: list[dict] = []
    files = {
        "search_agent": ROOT / "scripts" / "search_agent.py",
        "search_workflow": ROOT / ".github" / "workflows" / "ai_search_agent.yml",
        "validation_workflow": ROOT / ".github" / "workflows" / "auto_update.yml",
        "pending_importer": ROOT / "scripts" / "import_pending.py",
        "pending_test": ROOT / "scripts" / "test_import_pending_governance.py",
        "search_read_only_test": ROOT / "scripts" / "test_search_agent_canonical_read_only.py",
    }

    for label, path in files.items():
        require(path.exists(), f"required file exists: {label}", checks)

    agent = files["search_agent"].read_text(encoding="utf-8")
    search_wf = files["search_workflow"].read_text(encoding="utf-8")
    validation_wf = files["validation_workflow"].read_text(encoding="utf-8")
    importer = files["pending_importer"].read_text(encoding="utf-8")

    require("write_csv(master_path" not in agent, "search agent never writes master timeline", checks)
    require("write_csv(people_path" not in agent, "search agent never writes verified people", checks)
    require("master.at[" not in agent, "search agent never mutates master dataframe", checks)
    require("people.at[" not in agent, "search agent never mutates people dataframe", checks)
    require("--max-event-targets" in agent and "--max-person-targets" in agent,
            "search target bounds are implemented", checks)
    require("timeout=REQUEST_TIMEOUT_SECONDS" in agent,
            "source requests use a finite timeout", checks)

    require("data/master" not in commit_add_block(search_wf),
            "AI search commit surface excludes canonical records", checks)
    require("data/master" not in commit_add_block(validation_wf),
            "local validation commit surface excludes canonical records", checks)
    require("test_search_agent_canonical_read_only.py" in search_wf,
            "AI search workflow enforces canonical read-only test", checks)
    require("test_search_agent_canonical_read_only.py" in validation_wf,
            "local validation enforces canonical read-only test", checks)
    require("test_import_pending_governance.py" in validation_wf,
            "local validation enforces pending governance test", checks)

    require("--allow-master-promotion" in importer,
            "pending importer requires explicit promotion switch", checks)
    require("validation-only" in importer.lower(),
            "pending importer declares validation-only default", checks)
    require("template" in importer.lower(),
            "pending importer excludes template scaffolding", checks)

    master_files = sorted((ROOT / "data" / "master").glob("*.csv"))
    require(bool(master_files), "canonical dataset files are present", checks)

    payload = {
        "schema": "stegverse.free-dom.activation-readiness.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "result": "PASS",
        "checks": checks,
        "canonical_sha256": {p.relative_to(ROOT).as_posix(): sha256(p) for p in master_files},
        "verified_files_sha256": {label: sha256(path) for label, path in files.items()},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Activation readiness PASS: {len(checks)} checks; receipt={OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Activation readiness FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
