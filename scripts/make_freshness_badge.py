#!/usr/bin/env python3
"""
Generate a static SVG freshness badge using the most recent timestamp
in data/summary/ai_agent_summary.csv (column: 'last_seen' or 'ts_utc').

Output: docs/badges/freshness.svg
If the CSV is missing, empty, or columns not found, emit a graceful "unknown" badge.
"""
from __future__ import annotations
import sys
import csv
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
CSV_PATHS = [
    ROOT / "data" / "summary" / "ai_agent_summary.csv",
    ROOT / "data" / "summary" / "CHANGELOG_batches.csv",  # fallback
]
OUT = ROOT / "docs" / "badges" / "freshness.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

def parse_timestamp(s: str):
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except Exception:
            pass
    return None

def best_freshness() -> str:
    for path in CSV_PATHS:
        if not path.exists():
            continue
        try:
            with path.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                candidates = []
                for row in reader:
                    for col in ("last_seen", "ts_utc", "timestamp", "run_ts", "date"):
                        if col in row and row[col]:
                            dt = parse_timestamp(row[col])
                            if dt:
                                candidates.append(dt)
                if candidates:
                    latest = max(candidates)
                    return latest.strftime("%Y-%m-%d")
        except Exception:
            continue
    return "unknown"

def make_badge_svg(label: str, value: str) -> str:
    def w(text):
        return 6 * len(text) + 20
    lw = w(label)
    vw = w(value)
    total = lw + vw

    color = "#bdbdbd"
    if value != "unknown":
        try:
            dt = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days = (datetime.now(timezone.utc) - dt).days
            if days <= 2:
                color = "#2ca02c"
            elif days <= 7:
                color = "#ff7f0e"
            else:
                color = "#d62728"
        except Exception:
            color = "#bdbdbd"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="20" role="img" aria-label="freshness: {value}">
  <linearGradient id="g" x2="0" y2="100%">
    <stop offset="0" stop-color="#fff" stop-opacity=".7"/>
    <stop offset=".1" stop-opacity=".1"/>
    <stop offset=".9" stop-opacity=".3"/>
    <stop offset="1" stop-opacity=".5"/>
  </linearGradient>
  <mask id="m">
    <rect width="{total}" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#m)">
    <rect width="{lw}" height="20" fill="#555"/>
    <rect x="{lw}" width="{vw}" height="20" fill="{color}"/>
    <rect width="{total}" height="20" fill="url(#g)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="{lw/2:.1f}" y="14">freshness</text>
    <text x="{lw+vw/2:.1f}" y="14">{value}</text>
  </g>
</svg>"""

def main():
    value = best_freshness()
    svg = make_badge_svg("freshness", value)
    OUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT} with value '{value}'")

if __name__ == "__main__":
    main()
