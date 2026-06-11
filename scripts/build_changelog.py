#!/usr/bin/env python3
"""
FREE-DOM: build_changelog.py

Functions:
- Determines semantic version bump based on changed paths in latest commit.
- Updates data/summary/VERSION (creates if missing; default v1.0.0).
- Prepends a structured entry to CHANGELOG.md for the current commit (idempotent).
- Emits machine-readable snapshot at data/summary/CHANGELOG_batches.csv.
- Counts canonical rows (master) and open items (unverified).

SemVer rules (last commit diff vs HEAD~1):
  MAJOR:  Any change in .github/workflows/** OR core pipeline scripts:
          scripts/import_pending.py, scripts/update_timeline.py,
          scripts/search_agent.py, scripts/build_checklist.py
  MINOR:  Any change in scripts/** (other than above) OR data/sources/**
  PATCH:  All other changes (data updates, docs, README, diagrams, etc.)
"""

from __future__ import annotations
import os, re, csv, subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
P_MASTER = D / "master"
P_UNVER = D / "unverified"
P_SUMMARY = D / "summary"

CHANGELOG_MD = ROOT / "CHANGELOG.md"
CHANGELOG_CSV = P_SUMMARY / "CHANGELOG_batches.csv"
VERSION_FILE  = P_SUMMARY / "VERSION"

CORE_PIPELINE = {
    "scripts/import_pending.py",
    "scripts/update_timeline.py",
    "scripts/search_agent.py",
    "scripts/build_checklist.py",
}

# ---------- helpers -----------------------------------------------------------

def sh(args: list[str]) -> str:
    try:
        return subprocess.check_output(args, cwd=str(ROOT), text=True).strip()
    except Exception:
        return ""

def git_changed_files() -> list[str]:
    # Compare to previous commit if available
    has_prev = sh(["git", "rev-list", "--count", "HEAD"])
    if has_prev and int(has_prev) > 1:
        out = sh(["git", "diff", "--name-only", "HEAD~1", "HEAD"])
    else:
        out = sh(["git", "diff", "--name-only", "HEAD"])
    return [ln.strip() for ln in out.splitlines() if ln.strip()]

def current_version() -> tuple[int,int,int]:
    if VERSION_FILE.exists():
        raw = VERSION_FILE.read_text(encoding="utf-8").strip()
        m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", raw)
        if m:
            return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return (1, 0, 0)  # default v1.0.0

def write_version(ver: tuple[int,int,int]):
    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    VERSION_FILE.write_text(f"v{ver[0]}.{ver[1]}.{ver[2]}\n", encoding="utf-8")

def bump_version(kind: str, ver: tuple[int,int,int]) -> tuple[int,int,int]:
    major, minor, patch = ver
    if kind == "major":
        return (major+1, 0, 0)
    if kind == "minor":
        return (major, minor+1, 0)
    return (major, minor, patch+1)

def semver_kind(changed: list[str]) -> str:
    for p in changed:
        if p.startswith(".github/workflows/") or p in CORE_PIPELINE:
            return "major"
    for p in changed:
        if p.startswith("scripts/") or p.startswith("data/sources/"):
            return "minor"
    return "patch"

def read_rows(path: Path) -> int:
    if not path.exists(): return 0
    try:
        return len(pd.read_csv(path))
    except Exception:
        return 0

def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def git_ctx() -> Dict[str, Any]:
    return {
        "repo": os.getenv("GITHUB_REPOSITORY", ""),
        "branch": sh(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "commit_hash": sh(["git", "rev-parse", "HEAD"]),
        "commit_short": sh(["git", "rev-parse", "--short", "HEAD"]),
        "commit_subject": sh(["git", "log", "-1", "--pretty=%s"]),
        "commit_author": sh(["git", "log", "-1", "--pretty=%an"]),
        "commit_date_iso": sh(["git", "log", "-1", "--pretty=%cI"]) or now_utc(),
        "workflow": os.getenv("GITHUB_WORKFLOW", ""),
        "run_id": os.getenv("GITHUB_RUN_ID", ""),
        "actor": os.getenv("GITHUB_ACTOR", ""),
    }

def count_snapshot() -> Dict[str,int]:
    return {
        "master_timeline_rows": read_rows(P_MASTER / "master_timeline.csv"),
        "verified_people_rows": read_rows(P_MASTER / "verified_people_events.csv"),
        "unverified_events_rows": read_rows(P_UNVER / "unverified_events.csv"),
        "unverified_people_rows": read_rows(P_UNVER / "unverified_people.csv"),
        "unverified_connections_rows": read_rows(P_UNVER / "unverified_connections.csv"),
        "pending_event_batches": sum(1 for _ in (D / "pending" / "events").glob("*.csv")) if (D / "pending" / "events").exists() else 0,
        "pending_people_batches": sum(1 for _ in (D / "pending" / "people").glob("*.csv")) if (D / "pending" / "people").exists() else 0,
        "pending_unverified_batches": sum(1 for _ in (D / "pending" / "unverified").glob("*.csv")) if (D / "pending" / "unverified").exists() else 0,
    }

def load_batches_csv() -> pd.DataFrame:
    if CHANGELOG_CSV.exists():
        try:
            return pd.read_csv(CHANGELOG_CSV)
        except Exception:
            pass
    cols = [
        "version","ts_utc","branch","commit_hash","commit_short","commit_subject",
        "commit_author","commit_date_iso","workflow","run_id","actor",
        "master_timeline_rows","verified_people_rows",
        "unverified_events_rows","unverified_people_rows","unverified_connections_rows",
        "pending_event_batches","pending_people_batches","pending_unverified_batches"
    ]
    return pd.DataFrame(columns=cols)

def write_batches_csv(df: pd.DataFrame):
    P_SUMMARY.mkdir(parents=True, exist_ok=True)
    df.to_csv(CHANGELOG_CSV, index=False)

def prepend_md(entry: str):
    if CHANGELOG_MD.exists():
        current = CHANGELOG_MD.read_text(encoding="utf-8")
    else:
        current = ""
    header = "# 🧾 FREE-DOM — CHANGELOG\n\nAll notable changes are recorded by the `Auto Update` workflow.\n\n---\n\n"
    if current.startswith("# 🧾 FREE-DOM — CHANGELOG"):
        CHANGELOG_MD.write_text(entry + current, encoding="utf-8")
    else:
        CHANGELOG_MD.write_text(header + entry + current, encoding="utf-8")

def render_md(version: str, ctx: Dict[str,Any], cnt: Dict[str,int], changed: list[str]) -> str:
    date_d = ctx["commit_date_iso"][:10]
    lines = []
    lines.append(f"## {version} — {date_d}")
    lines.append(f"**Commit:** `{ctx['commit_short']}` — {ctx['commit_subject']}  ")
    lines.append(f"**Author:** {ctx['commit_author']}  **Branch:** `{ctx['branch']}`  **Workflow:** `{ctx['workflow']}` (run {ctx['run_id']})\n")
    lines.append("<details><summary>Changed files</summary>\n\n```txt")
    lines.extend(changed or ["(no diff available)"])
    lines.append("```\n</details>\n")
    lines.append("| Dataset | Count |")
    lines.append("|---|---:|")
    lines.append(f"| master_timeline.csv | {cnt['master_timeline_rows']} |")
    lines.append(f"| verified_people_events.csv | {cnt['verified_people_rows']} |")
    lines.append(f"| unverified_events.csv | {cnt['unverified_events_rows']} |")
    lines.append(f"| unverified_people.csv | {cnt['unverified_people_rows']} |")
    lines.append(f"| unverified_connections.csv | {cnt['unverified_connections_rows']} |")
    lines.append("")
    lines.append("| Pending Batches | Count |")
    lines.append("|---|---:|")
    lines.append(f"| data/pending/events | {cnt['pending_event_batches']} |")
    lines.append(f"| data/pending/people | {cnt['pending_people_batches']} |")
    lines.append(f"| data/pending/unverified | {cnt['pending_unverified_batches']} |")
    lines.append("\n---\n\n")
    return "\n".join(lines)

# ---------- main --------------------------------------------------------------

def main():
    # Determine bump kind from changes
    changed = git_changed_files()
    kind = semver_kind(changed)
    cur = current_version()
    new = bump_version(kind, cur)

    # Write version file
    write_version(new)
    version_str = f"v{new[0]}.{new[1]}.{new[2]}"

    # Context & counts
    ctx = git_ctx()
    cnt = count_snapshot()

    # Update summary CSV (top = latest)
    df = load_batches_csv()
    if not ((df.get("commit_hash") == ctx["commit_hash"]).any()):
        row = {
            "version": version_str,
            "ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            **ctx, **cnt
        }
        df = pd.concat([pd.DataFrame([row]), df], ignore_index=True)
        write_batches_csv(df)

    # Prepend MD entry
    md_entry = render_md(version_str, ctx, cnt, changed)
    prepend_md(md_entry)

    # Console summary
    print(f"Version bump: {kind.upper()}  {cur} -> {new}")
    print(f"Changed files ({len(changed)}):")
    for p in changed: print(" -", p)

if __name__ == "__main__":
    main()
