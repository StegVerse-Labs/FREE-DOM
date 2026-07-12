#!/usr/bin/env python3
"""
AI Search Agent (Public OSINT Only)
Portable (supports --base):
- Reads <base>/data/sources/sources_whitelist.csv
- Scans <base>/data/master/master_timeline.csv for deep_search_event: pending
- Scans <base>/data/master/verified_people_events.csv for deep_search_person: pending
- Crawls whitelisted sources (RSS & allowed pages)
- Appends lead links into notes fields (non-destructive)
- Emits ST-007 evidence manifests, transition receipts, and a run Merkle batch
- Emits a bounded run receipt even when zero hits are found
- Logs under <base>/data/logs/ai_agent/
- NEVER accesses non-public or “dark web” content
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
from datetime import datetime, timezone
from typing import Dict, List

import feedparser
import pandas as pd
import requests
from bs4 import BeautifulSoup

from evidence_chain import persist_discovery, write_run_merkle_batch
from search_run_evidence import persist_search_run

USER_AGENT = "StegVerse-AI-Agent/1.2 (+public sources only; ST-007 receipts)"
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})


def normalize_spaces(s: str) -> str:
    return " ".join((s or "").split())


def safe_get(url: str, timeout: int = 20) -> tuple[str, str | None]:
    try:
        response = SESSION.get(url, timeout=timeout)
        if response.status_code == 200 and "text/html" in response.headers.get("content-type", ""):
            return response.text, None
        return "", f"status={response.status_code} content_type={response.headers.get('content-type', '')}"
    except Exception as exc:
        return "", f"{type(exc).__name__}: {exc}"


def read_whitelist(path: pathlib.Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def search_rss(feeds: List[str], keywords: List[str], failures: list[dict], limit_per_feed: int = 30) -> List[Dict]:
    results: List[Dict] = []
    kw = [k.lower() for k in keywords if k]
    for url in feeds:
        try:
            parsed = feedparser.parse(url)
            if getattr(parsed, "bozo", False):
                failures.append({"source": url, "stage": "rss-parse", "error": str(getattr(parsed, "bozo_exception", "unknown parse error"))})
            for entry in (parsed.entries[:limit_per_feed] if hasattr(parsed, "entries") else []):
                text = " ".join([
                    entry.get("title", ""),
                    entry.get("summary", ""),
                    " ".join([t.get("term", "") for t in entry.get("tags", []) if isinstance(t, dict)]),
                ]).lower()
                if all(k in text for k in kw):
                    results.append({
                        "feed": url,
                        "title": entry.get("title", "").strip(),
                        "link": entry.get("link", "").strip(),
                        "published": entry.get("published", "").strip(),
                    })
        except Exception as exc:
            failures.append({"source": url, "stage": "rss-search", "error": f"{type(exc).__name__}: {exc}"})
    return results


def site_keyword_scan(pages: List[str], keywords: List[str], failures: list[dict], limit_per_site: int = 10) -> List[Dict]:
    out: List[Dict] = []
    kw = [k.lower() for k in keywords if k]
    for base in pages:
        html, error = safe_get(base)
        if error:
            failures.append({"source": base, "stage": "site-fetch", "error": error})
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        anchors = soup.find_all("a", href=True)
        count = 0
        for anchor in anchors:
            text = (anchor.get_text(" ", strip=True) or "").lower()
            href = anchor["href"]
            if all(k in text for k in kw) and href.startswith("http"):
                out.append({"page": base, "title": anchor.get_text(" ", strip=True), "link": href})
                count += 1
                if count >= limit_per_site:
                    break
    return out


def load_csv(path: pathlib.Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def write_csv(path: pathlib.Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def find_pending(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if df.empty or col not in df.columns:
        return pd.DataFrame()
    return df[df[col].fillna("").str.lower().isin(["", "pending"])]


def make_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def mk_log(log_dir: pathlib.Path, run_id: str) -> pathlib.Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"agent_run_{run_id}.jsonl"


def log_line(log_path: pathlib.Path, payload: Dict) -> None:
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def keywords_for_event(row: pd.Series) -> List[str]:
    base = " ".join([str(row.get("event", "")), str(row.get("location", ""))])
    tokens = [t for t in re.split(r"[^A-Za-z0-9]+", base) if len(t) >= 3]
    return list(dict.fromkeys([t.lower() for t in tokens]))[:6]


def keywords_for_person(row: pd.Series) -> List[str]:
    base = " ".join([str(row.get("person", "")), str(row.get("event", "")), str(row.get("location", ""))])
    tokens = [t for t in re.split(r"[^A-Za-z0-9]+", base) if len(t) >= 3]
    return list(dict.fromkeys([t.lower() for t in tokens]))[:6]


def row_key(row: pd.Series, fields: list[str]) -> str:
    return "|".join(normalize_spaces(str(row.get(field, ""))) for field in fields)


def persist_hits(
    *,
    base: pathlib.Path,
    hits: list[dict],
    target_type: str,
    target_label: str,
    target_row_key: str,
    keywords: list[str],
    run_id: str,
    log_path: pathlib.Path,
    receipt_refs: list[dict[str, str]],
) -> None:
    for hit in hits:
        try:
            ref = persist_discovery(
                base=base,
                hit=hit,
                target_type=target_type,
                target_label=target_label,
                target_row_key=target_row_key,
                keywords=keywords,
                run_id=run_id,
            )
            receipt_refs.append(ref)
            log_line(log_path, {"type": "evidence-receipt", **ref})
        except Exception as exc:
            log_line(log_path, {
                "type": "evidence-emission-failure",
                "target_type": target_type,
                "target_label": target_label,
                "link": hit.get("link"),
                "error": f"{type(exc).__name__}: {exc}",
            })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=".", help="Scope base directory (repo root or nested scope folder)")
    args = parser.parse_args()

    started_at = iso_now()
    base = pathlib.Path(args.base).resolve()
    data = base / "data"
    master_path = data / "master" / "master_timeline.csv"
    people_path = data / "master" / "verified_people_events.csv"
    whitelist_path = data / "sources" / "sources_whitelist.csv"
    log_dir = data / "logs" / "ai_agent"

    run_id = make_run_id()
    log_path = mk_log(log_dir, run_id)
    whitelist = read_whitelist(whitelist_path)
    rss_feeds = [r["url"] for r in whitelist if r.get("url") and r.get("type", "rss").lower() == "rss"]
    site_pages = [r["url"] for r in whitelist if r.get("url") and r.get("type", "rss").lower() != "rss"]

    master = load_csv(master_path)
    people = load_csv(people_path)
    pending_events = find_pending(master, "deep_search_event")
    pending_people = find_pending(people, "deep_search_person")

    total_hits = 0
    failures: list[dict] = []
    receipt_refs: list[dict[str, str]] = []

    for _, row in pending_events.iterrows():
        keywords = keywords_for_event(row)
        if not keywords:
            continue
        hits = search_rss(rss_feeds, keywords, failures, 25)[:5] + site_keyword_scan(site_pages, keywords, failures, 8)[:5]
        if hits:
            total_hits += len(hits)
            notes = normalize_spaces(str(row.get("notes", "")))
            append = " Leads: " + "; ".join(hit["link"] for hit in hits)
            master.at[row.name, "notes"] = (notes + append).strip()
            target_label = normalize_spaces(str(row.get("event", "")))
            target_key = row_key(row, ["date", "location", "event"])
            log_line(log_path, {"type": "event", "base": str(base), "keywords": keywords, "hits": hits, "target_row_key": target_key})
            persist_hits(
                base=base,
                hits=hits,
                target_type="event",
                target_label=target_label,
                target_row_key=target_key,
                keywords=keywords,
                run_id=run_id,
                log_path=log_path,
                receipt_refs=receipt_refs,
            )

    for _, row in pending_people.iterrows():
        keywords = keywords_for_person(row)
        if not keywords:
            continue
        hits = search_rss(rss_feeds, keywords, failures, 25)[:5] + site_keyword_scan(site_pages, keywords, failures, 8)[:5]
        if hits:
            total_hits += len(hits)
            notes = normalize_spaces(str(row.get("deep_search_notes", "")))
            append = " Leads: " + "; ".join(hit["link"] for hit in hits)
            people.at[row.name, "deep_search_notes"] = (notes + append).strip()
            target_label = normalize_spaces(str(row.get("person", "")))
            target_key = row_key(row, ["person", "date", "location", "event"])
            log_line(log_path, {"type": "person", "base": str(base), "keywords": keywords, "hits": hits, "target_row_key": target_key})
            persist_hits(
                base=base,
                hits=hits,
                target_type="person",
                target_label=target_label,
                target_row_key=target_key,
                keywords=keywords,
                run_id=run_id,
                log_path=log_path,
                receipt_refs=receipt_refs,
            )

    if not master.empty:
        write_csv(master_path, master)
    if not people.empty:
        write_csv(people_path, people)

    for failure in failures:
        log_line(log_path, {"type": "source-check-failure", **failure})

    completed_at = iso_now()
    run_ref = persist_search_run(
        base=base,
        run_id=run_id,
        started_at=started_at,
        completed_at=completed_at,
        event_targets=len(pending_events),
        person_targets=len(pending_people),
        rss_sources=len(rss_feeds),
        page_sources=len(site_pages),
        total_hits=total_hits,
        hit_receipts=len(receipt_refs),
        failures=failures,
        log_path=log_path,
    )
    receipt_refs.append(run_ref)
    log_line(log_path, {"type": "search-run-evidence-receipt", **run_ref})

    batch_path = write_run_merkle_batch(base, run_id, receipt_refs)
    log_line(log_path, {
        "summary": {
            "base": str(base),
            "run_id": run_id,
            "started_at": started_at,
            "completed_at": completed_at,
            "pending_event_targets": len(pending_events),
            "pending_person_targets": len(pending_people),
            "rss_sources": len(rss_feeds),
            "page_sources": len(site_pages),
            "total_hits": total_hits,
            "hit_evidence_receipts": len(receipt_refs) - 1,
            "run_evidence_receipts": 1,
            "source_failures": len(failures),
            "merkle_batch": batch_path.relative_to(base).as_posix() if batch_path else None,
        }
    })


if __name__ == "__main__":
    main()
