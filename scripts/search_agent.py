#!/usr/bin/env python3
"""
AI Search Agent (Public OSINT Only)
Portable (supports --base):
- Reads <base>/data/sources/sources_whitelist.csv
- Scans <base>/data/master/master_timeline.csv for deep_search_event: pending
- Scans <base>/data/master/verified_people_events.csv for deep_search_person: pending
- Crawls whitelisted sources (RSS & allowed pages)
- Appends lead links into notes fields (non-destructive)
- Logs under <base>/data/logs/ai_agent/
- NEVER accesses non-public or “dark web” content
"""

from __future__ import annotations
import argparse, csv, re, json, pathlib, hashlib
from datetime import datetime
from typing import List, Dict

import pandas as pd
import feedparser
import requests
from bs4 import BeautifulSoup

USER_AGENT = "StegVerse-AI-Agent/1.0 (+public sources only)"
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

def normalize_spaces(s: str) -> str:
    return " ".join((s or "").split())

def safe_get(url: str, timeout: int = 20) -> str:
    try:
        r = SESSION.get(url, timeout=timeout)
        if r.status_code == 200 and "text/html" in r.headers.get("content-type",""):
            return r.text
        return ""
    except Exception:
        return ""

def read_whitelist(path: pathlib.Path) -> List[Dict[str,str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def search_rss(feeds: List[str], keywords: List[str], limit_per_feed: int = 30) -> List[Dict]:
    results: List[Dict] = []
    kw = [k.lower() for k in keywords if k]
    for url in feeds:
        try:
            parsed = feedparser.parse(url)
            for entry in (parsed.entries[:limit_per_feed] if hasattr(parsed, "entries") else []):
                text = " ".join([
                    entry.get("title",""),
                    entry.get("summary",""),
                    " ".join([t.get("term","") for t in entry.get("tags", []) if isinstance(t, dict)])
                ]).lower()
                if all(k in text for k in kw):
                    results.append({
                        "feed": url,
                        "title": entry.get("title","").strip(),
                        "link": entry.get("link","").strip(),
                        "published": entry.get("published","").strip()
                    })
        except Exception:
            continue
    return results

def site_keyword_scan(pages: List[str], keywords: List[str], limit_per_site: int = 10) -> List[Dict]:
    out: List[Dict] = []
    kw = [k.lower() for k in keywords if k]
    for base in pages:
        html = safe_get(base)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        anchors = soup.find_all("a", href=True)
        count = 0
        for a in anchors:
            txt = (a.get_text(" ", strip=True) or "").lower()
            href = a["href"]
            if all(k in txt for k in kw) and href.startswith("http"):
                out.append({"page": base, "title": a.get_text(" ", strip=True), "link": href})
                count += 1
                if count >= limit_per_site:
                    break
    return out

def load_csv(path: pathlib.Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()

def write_csv(path: pathlib.Path, df: pd.DataFrame):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)

def find_pending(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if df.empty or col not in df.columns:
        return pd.DataFrame()
    return df[(df[col].fillna("").str.lower().isin(["", "pending"]))]

def mk_log(log_dir: pathlib.Path) -> pathlib.Path:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"agent_run_{ts}.jsonl"

def log_line(log_path: pathlib.Path, payload: Dict):
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

def keywords_for_event(row: pd.Series) -> List[str]:
    base = " ".join([str(row.get("event","")), str(row.get("location",""))])
    tokens = [t for t in re.split(r"[^A-Za-z0-9]+", base) if len(t) >= 3]
    return list(dict.fromkeys([t.lower() for t in tokens]))[:6]

def keywords_for_person(row: pd.Series) -> List[str]:
    base = " ".join([str(row.get("person","")), str(row.get("event","")), str(row.get("location",""))])
    tokens = [t for t in re.split(r"[^A-Za-z0-9]+", base) if len(t) >= 3]
    return list(dict.fromkeys([t.lower() for t in tokens]))[:6]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=".", help="Scope base directory (repo root or nested scope folder)")
    args = ap.parse_args()

    BASE = pathlib.Path(args.base).resolve()
    DATA = BASE / "data"

    MASTER = DATA / "master" / "master_timeline.csv"
    PEOPLE = DATA / "master" / "verified_people_events.csv"
    WHITELIST = DATA / "sources" / "sources_whitelist.csv"
    LOG_DIR = DATA / "logs" / "ai_agent"

    log_path = mk_log(LOG_DIR)

    wl = read_whitelist(WHITELIST)
    rss_feeds = [r["url"] for r in wl if (r.get("type","rss").lower() == "rss")]
    site_pages = [r["url"] for r in wl if (r.get("type","rss").lower() != "rss")]

    master = load_csv(MASTER)
    people = load_csv(PEOPLE)

    pending_events = find_pending(master, "deep_search_event")
    pending_people = find_pending(people, "deep_search_person")

    total_hits = 0

    for _, row in pending_events.iterrows():
        kws = keywords_for_event(row)
        if not kws:
            continue
        hits = search_rss(rss_feeds, kws, 25)[:5] + site_keyword_scan(site_pages, kws, 8)[:5]
        if hits:
            total_hits += len(hits)
            notes = normalize_spaces(str(row.get("notes","")))
            append = " Leads: " + "; ".join([h["link"] for h in hits])
            master.at[row.name, "notes"] = (notes + append).strip()
            log_line(log_path, {"type":"event", "base": str(BASE), "keywords": kws, "hits": hits})

    for _, row in pending_people.iterrows():
        kws = keywords_for_person(row)
        if not kws:
            continue
        hits = search_rss(rss_feeds, kws, 25)[:5] + site_keyword_scan(site_pages, kws, 8)[:5]
        if hits:
            total_hits += len(hits)
            notes = normalize_spaces(str(row.get("deep_search_notes","")))
            append = " Leads: " + "; ".join([h["link"] for h in hits])
            people.at[row.name, "deep_search_notes"] = (notes + append).strip()
            log_line(log_path, {"type":"person", "base": str(BASE), "keywords": kws, "hits": hits})

    if not master.empty:
        write_csv(MASTER, master)
    if not people.empty:
        write_csv(PEOPLE, people)

    log_line(log_path, {"summary": {"base": str(BASE), "total_hits": total_hits}})

if __name__ == "__main__":
    main()
