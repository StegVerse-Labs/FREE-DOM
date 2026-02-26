#!/usr/bin/env python3
"""
Builds two analytics files from AI Search Agent logs (portable via --base):
- <base>/data/summary/ai_agent_summary.csv
- <base>/data/summary/ai_agent_sources_index.csv
Reads logs from: <base>/data/logs/ai_agent/agent_run_*.jsonl
"""

from __future__ import annotations
import argparse, json, csv, pathlib, urllib.parse

def domain_of(url: str) -> str:
    try:
        netloc = urllib.parse.urlparse(url).netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:
        return ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=".", help="Scope base directory")
    args = ap.parse_args()

    BASE = pathlib.Path(args.base).resolve()
    DATA = BASE / "data"
    LOGS = DATA / "logs" / "ai_agent"
    OUT_SUM = DATA / "summary" / "ai_agent_summary.csv"
    OUT_SRC = DATA / "summary" / "ai_agent_sources_index.csv"

    OUT_SUM.parent.mkdir(parents=True, exist_ok=True)

    seen_sources = {}
    if OUT_SRC.exists():
        with OUT_SRC.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                seen_sources[r["source_domain"]] = {
                    "first_seen_run": r.get("first_seen_run",""),
                    "last_seen_run": r.get("last_seen_run",""),
                    "total_hits": int(r.get("total_hits","0") or 0),
                    "unique_links": int(r.get("unique_links","0") or 0),
                }

    def iter_runs():
        if not LOGS.exists():
            return
        for p in sorted(LOGS.glob("agent_run_*.jsonl")):
            ts = p.stem.replace("agent_run_","",1)
            yield ts, p

    summary_rows = []
    global_seen_links = set()

    for ts, path in iter_runs():
        total_hits = 0
        links_this_run = set()
        sources_this_run = []

        with path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if "hits" in obj and isinstance(obj["hits"], list):
                    for h in obj["hits"]:
                        link = (h.get("link") or "").strip()
                        if not link:
                            continue
                        total_hits += 1
                        links_this_run.add(link)
                        src = domain_of(link)
                        if src:
                            sources_this_run.append(src)
                            if src not in seen_sources:
                                seen_sources[src] = {
                                    "first_seen_run": ts,
                                    "last_seen_run": ts,
                                    "total_hits": 1,
                                    "unique_links": 1,
                                }
                            else:
                                seen_sources[src]["last_seen_run"] = ts
                                seen_sources[src]["total_hits"] += 1
                                seen_sources[src]["unique_links"] += 1

        unique_links = len(links_this_run)
        new_leads = len([l for l in links_this_run if l not in global_seen_links])
        global_seen_links |= links_this_run

        sources_set = list(dict.fromkeys(sorted(sources_this_run)))
        new_sources = [s for s in sources_set if seen_sources.get(s, {}).get("first_seen_run","") == ts]

        summary_rows.append({
            "run_timestamp": ts,
            "total_hits": total_hits,
            "new_leads": new_leads,
            "unique_links": unique_links,
            "sources_count": len(sources_set),
            "new_sources_count": len(new_sources),
            "sources": ";".join(sources_set),
            "new_sources": ";".join(new_sources),
        })

    with OUT_SUM.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "run_timestamp","total_hits","new_leads","unique_links",
            "sources_count","new_sources_count","sources","new_sources"
        ])
        w.writeheader()
        for r in summary_rows:
            w.writerow(r)

    with OUT_SRC.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "source_domain","first_seen_run","last_seen_run","total_hits","unique_links"
        ])
        w.writeheader()
        for src, agg in sorted(seen_sources.items(), key=lambda kv: kv[0]):
            w.writerow({"source_domain": src, **agg})

    print(f"Wrote {OUT_SUM} and {OUT_SRC}")

if __name__ == "__main__":
    main()
