"""G17 workflow-surface registry for StegVerse-Labs/FREE-DOM: the workflow files equal the registry's
surfaces[]; the stable dispatcher has no gated trigger; kept surfaces and folded
records are sha256-pinned; the catalog verifies ALLOW and covers every folded job.
Stdlib only (runs under tools/tasks/run_plain_tests.py or unittest)."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "control/workflow-surface-registry.json").read_text())
CATALOG = json.loads((ROOT / "tools/tasks/task_catalog.json").read_text())
GATED = ("workflow_dispatch", "schedule", "repository_dispatch", "issues", "workflow_run")


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_workflow_files_equal_registered_surfaces():
    actual = sorted(p.name for p in (ROOT / ".github/workflows").iterdir() if p.suffix in (".yml", ".yaml"))
    registered = sorted(Path(s["path"]).name for s in REGISTRY["surfaces"])
    assert actual == registered, (actual, registered)
    assert len(actual) <= REGISTRY["exception_repository_workflow_count_max"]
    if len(actual) > REGISTRY["preferred_repository_workflow_count_max"]:
        for x in REGISTRY["surfaces"]:
            if x["classification"] != "KEEP_STABLE_DISPATCHER":
                assert x["exception"]["lifecycle"] and x["exception"]["justification"], x["path"]


def test_dispatcher_has_no_gated_trigger_and_kept_surfaces_pinned():
    for s in REGISTRY["surfaces"]:
        path = ROOT / s["path"]
        if s["classification"] == "KEEP_STABLE_DISPATCHER":
            text = path.read_text()
            assert text.count("\non:\n") == 1, s["path"]
            on = text.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
            for t in GATED:
                assert f"  {t}:" not in on, (s["path"], t)
        else:
            assert _sha(path) == s["verbatim_sha256"], s["path"]


def test_folded_records_pinned_and_covered():
    groups = {g["id"]: g for g in CATALOG["groups"]}
    for f in REGISTRY["folded"]:
        path = ROOT / f["verbatim_record"]
        assert _sha(path) == f["verbatim_sha256"], f["workflow"]
        assert not (ROOT / f["workflow"]).exists(), f["workflow"]
        for gid in f.get("catalog_groups", []):
            assert gid in groups, gid
            assert set(groups[gid]["events"]) == {"pull_request", "push"}
        if f["classification"] == "CONSOLIDATE_INTO_STABLE_DISPATCHER":
            assert f.get("catalog_groups"), f["workflow"]


def test_catalog_verifies_allow():
    proc = subprocess.run([sys.executable, str(ROOT / "tools/tasks/run_catalog.py"), "verify"],
                          capture_output=True, text=True)
    assert proc.returncode == 0 and json.loads(proc.stdout)["disposition"] == "ALLOW", proc.stdout


class RegistryTests(unittest.TestCase):
    def test_all(self):
        for fn in (test_workflow_files_equal_registered_surfaces, test_dispatcher_has_no_gated_trigger_and_kept_surfaces_pinned,
                   test_folded_records_pinned_and_covered, test_catalog_verifies_allow):
            fn()


if __name__ == "__main__":
    unittest.main()
