#!/usr/bin/env python3
"""Stdlib collector for plain pytest-style test files (no pytest dependency).

Usage: python tools/tasks/run_plain_tests.py tests/test_a.py [tests/test_b.py ...]

Imports each file, calls every top-level ``test_*`` function in definition order,
and supplies the only fixture these tests use, ``tmp_path`` (a fresh
pathlib.Path temp directory). Any other parameter fails closed rather than being
guessed. Exits 0 only if every collected test passes and at least one ran.
G17 fold of StegVerse-org/demo_ingest_engine (StegVerse-org/.github#166).
"""
from __future__ import annotations

import importlib.util
import inspect
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str]) -> int:
    if not argv:
        print("FAIL_CLOSED no test files given")
        return 2
    sys.path.insert(0, str(ROOT))
    ran = failed = 0
    for rel in argv:
        path = (ROOT / rel).resolve()
        spec = importlib.util.spec_from_file_location(f"plain_{path.stem}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name, fn in list(vars(module).items()):
            if not (name.startswith("test_") and inspect.isfunction(fn) and fn.__module__ == module.__name__):
                continue
            params = list(inspect.signature(fn).parameters)
            unknown = [p for p in params if p != "tmp_path"]
            ran += 1
            if unknown:
                failed += 1
                print(f"FAIL {rel}::{name} unsupported fixture(s) {unknown}")
                continue
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    fn(**({"tmp_path": Path(tmp)} if params else {}))
                print(f"PASS {rel}::{name}")
            except Exception:
                failed += 1
                print(f"FAIL {rel}::{name}")
                traceback.print_exc()
    print(f"{ran - failed} passed, {failed} failed")
    return 0 if ran and not failed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
