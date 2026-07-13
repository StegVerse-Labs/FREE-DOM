#!/usr/bin/env python3
"""Governed public-source search agent.

The agent reads canonical records only to identify declared search targets. It never
writes to ``data/master``. Discoveries are emitted as unverified evidence records,
transition receipts, logs, summaries, and a run Merkle batch.
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

USER_AGENT = "StegVerse-AI-Agent/1.3 (+public sources only; canonical-read-only)"
REQUEST_TIMEOUT_SECONDS = 15
SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
)


def normalize_spaces(value: str) -> str:
    return " ".join((value or "").split())


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def make_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_whitelist(path: pathlib.Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_csv_read_only(path: pathlib.Path) -> pd.DataFrame:
    """Load canonical input without creating or rewriting it."""
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def find_pending(dataframe: pd.DataFrame, column: str, limit: int) -> pd.DataFrame:
    if dataframe.empty or column not in dataframe.columns or limit <= 0:
        return pd.DataFrame()
    values = dataframe[column].fillna("").astype(str).str.lower()
    return dataframe[values.isin(["", "pending"])].head(limit).copy()


def keywords_for_event(row: pd.Series) -> List[str]:
    base = " ".join([str(row.get("event", "")), str(row.get("location", ""))])
    tokens = [token for token in re.split(r"[^A-Za-z0-9]+", base) if len(token) >= 3]
    return list(dict.fromkeys(token.lower() for token in tokens))[:6]


def keywords_for_person(row: pd.Series) -> List[str]:
    base = " ".join(
        [
            str(row.get("person", "")),
            str(row.get("event", "")),
            str(row.get("location", "")),
        ]
    )
    tokens = [token for token in re.split(r"[^A-Za-z0-9]+", base) if len(token) >= 3]
    return list(dict.fromkeys(token.lower() for token in tokens))[:6]


def row_key(row: pd.Series, fields: list[str]) -> str:
    return "|".join(normalize_spaces(str(row.get(field, ""))) for field in fields)


def mk_log(log_dir: pathlib.Path, run_id: str) -> pathlib.Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"agent_run_{run_id}.jsonl"


def log_line(log_path: pathlib.Path, payload: Dict) -> None:
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def fetch_public(url: str) -> tuple[bytes, str, str | None]:
    try:
        response = SESSION.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        content_type = response.headers.get("content-type", "")
        if response.status_code != 200:
            return b"", content_type, f"status={response.status_code}"
        return response.content, content_type, None
    except Exception as exc:  # network failures are evidence, not silent absence
        return b"", "", f"{type(exc).__name__}: {exc}"


def search_rss(
    feeds: List[str],
    keywords: List[str],
    failures: list[dict],
    limit_per_feed: int = 25,
) -> List[Dict]:
    results: List[Dict] = []
    required = [keyword.lower() for keyword in keywords if keyword]
    for url in feeds:
        payload, _, error = fetch_public(url)
        if error:
            failures.append({"source": url, "stage": "rss-fetch", "error": error})
            continue
        try:
            parsed = feedparser.parse(payload)
            if getattr(parsed, "bozo", False):
                failures.append(
                    {
                        "source": url,
                        "stage": "rss-parse",
                        "error": str(getattr(parsed, "bozo_exception", "unknown parse error")),
                    }
                )
            for entry in getattr(parsed, "entries", [])[:limit_per_feed]:
                text = " ".join(
                    [
                        entry.get("title", ""),
                        entry.get("summary", ""),
                        " ".join(
                            tag.get("term", "")
                            for tag in entry.get("tags", [])
                            if isinstance(tag, dict)
                        ),
                    ]
                ).lower()
                if all(keyword in text for keyword in required):
                    results.append(
                        {
                            "feed": url,
                            "title": entry.get("title", "").strip(),
                            "link": entry.get("link", "").strip(),
                            "published": entry.get("published", "").strip(),
                        }
                    )
        except Exception as exc:
            failures.append(
                {"source": url, "stage": "rss-search", "error": f"{type(exc).__name__}: {exc}"}
            )
    return results


def site_keyword_scan(
    pages: List[str],
    keywords: List[str],
    failures: list[dict],
    limit_per_site: int = 8,
) -> List[Dict]:
    results: List[Dict] = []
    required = [keyword.lower() for keyword in keywords if keyword]
    for url in pages:
        payload, content_type, error = fetch_public(url)
        if error:
            failures.append({"source": url, "stage": "site-fetch", "error": error})
            continue
        if "html" not in content_type.lower():
            failures.append(
                {"source": url, "stage": "site-fetch", "error": f"unsupported content_type={content_type}"}
            )
            continue
        soup = BeautifulSoup(payload, "html.parser")
        count = 0
        for anchor in soup.find_all("a", href=True):
            text = (anchor.get_text(" ", strip=True) or "").lower()
            href = str(anchor["href"])
            if all(keyword in text for keyword in required) and href.startswith(("http://", "https://")):
                results.append({"page": url, "title": anchor.get_text(" ", strip=True), "link": href})
                count += 1
                if count >= limit_per_site:
                    break
    return results


def deduplicate_hits(hits: list[dict], limit: int = 10) -> list[dict]:
    output: list[dict] = []
    seen: set[str] = set()
    for hit in hits:
        link = normalize_spaces(str(hit.get("link", "")))
        if not link or link in seen:
            continue
        seen.add(link)
        output.append(hit)
        if len(output) >= limit:
            break
    return output


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
            reference = persist_discovery(
                base=base,
                hit=hit,
                target_type=target_type,
                target_label=target_label,
                target_row_key=target_row_key,
                keywords=keywords,
                run_id=run_id,
            )
            receipt_refs.append(reference)
            log_line(log_path, {"type": "evidence-receipt", **reference})
        except Exception as exc:
            log_line(
                log_path,
                {
                    "type": "evidence-emission-failure",
                    "target_type": target_type,
                    "target_label": target_label,
                    "link": hit.get("link"),
                    "error": f"{type(exc).__name__}: {exc}",
                },
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=".", help="Repository root or portable scope directory")
    parser.add_argument("--max-event-targets", type=int, default=25)
    parser.add_argument("--max-person-targets", type=int, default=25)
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
    rss_feeds = [row["url"] for row in whitelist if row.get("url") and row.get("type", "rss").lower() == "rss"]
    site_pages = [row["url"] for row in whitelist if row.get("url") and row.get("type", "rss").lower() != "rss"]

    master = load_csv_read_only(master_path)
    people = load_csv_read_only(people_path)
    pending_events = find_pending(master, "deep_search_event", args.max_event_targets)
    pending_people = find_pending(people, "deep_search_person", args.max_person_targets)

    failures: list[dict] = []
    receipt_refs: list[dict[str, str]] = []
    total_hits = 0

    for _, row in pending_events.iterrows():
        keywords = keywords_for_event(row)
        if not keywords:
            continue
        hits = deduplicate_hits(
            search_rss(rss_feeds, keywords, failures)
            + site_keyword_scan(site_pages, keywords, failures)
        )
        total_hits += len(hits)
        target_key = row_key(row, ["date", "location", "event"])
        log_line(
            log_path,
            {
                "type": "event-search",
                "keywords": keywords,
                "hits": hits,
                "target_row_key": target_key,
                "canonical_write": False,
            },
        )
        persist_hits(
            base=base,
            hits=hits,
            target_type="event",
            target_label=normalize_spaces(str(row.get("event", ""))),
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
        hits = deduplicate_hits(
            search_rss(rss_feeds, keywords, failures)
            + site_keyword_scan(site_pages, keywords, failures)
        )
        total_hits += len(hits)
        target_key = row_key(row, ["person", "date", "location", "event"])
        log_line(
            log_path,
            {
                "type": "person-search",
                "keywords": keywords,
                "hits": hits,
                "target_row_key": target_key,
                "canonical_write": False,
            },
        )
        persist_hits(
            base=base,
            hits=hits,
            target_type="person",
            target_label=normalize_spaces(str(row.get("person", ""))),
            target_row_key=target_key,
            keywords=keywords,
            run_id=run_id,
            log_path=log_path,
            receipt_refs=receipt_refs,
        )

    for failure in failures:
        log_line(log_path, {"type": "source-check-failure", **failure})

    completed_at = iso_now()
    run_reference = persist_search_run(
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
    receipt_refs.append(run_reference)
    log_line(log_path, {"type": "search-run-evidence-receipt", **run_reference})

    batch_path = write_run_merkle_batch(base, run_id, receipt_refs)
    log_line(
        log_path,
        {
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
                "canonical_writes": 0,
                "merkle_batch": batch_path.relative_to(base).as_posix() if batch_path else None,
            }
        },
    )
    print(f"ALLOW governed_search_run={run_id} canonical_writes=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
