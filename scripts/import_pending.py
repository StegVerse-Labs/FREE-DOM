#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import pathlib
from datetime import datetime
from typing import Iterable


# ----------------------------
# Strict CSV guards (NEW)
# ----------------------------

class CsvSchemaError(RuntimeError):
    pass


def _read_csv_raw(path: pathlib.Path) -> list[list[str]]:
    """
    Read CSV as raw rows (including header), without DictReader magic,
    so we can strictly validate column counts.
    """
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        return [row for row in r]


def _validate_rectangular_csv(path: pathlib.Path) -> tuple[list[str], list[list[str]]]:
    """
    Ensure every row has the same number of columns as the header.
    Returns (header, data_rows).
    """
    rows = _read_csv_raw(path)
    if not rows:
        return ([], [])
    header = rows[0]
    if not header:
        raise CsvSchemaError(f"{path.as_posix()}: empty header row")

    width = len(header)
    for i, row in enumerate(rows[1:], start=2):  # 1-indexed lines; start=2 for first data row
        if len(row) != width:
            raise CsvSchemaError(
                f"{path.as_posix()}: row {i} has {len(row)} columns; expected {width}. "
                f"(Fix the CSV so every row matches the header column count.)"
            )
    return (header, rows[1:])


def _read_csv_strict_dicts(path: pathlib.Path) -> list[dict]:
    """
    Strict CSV reader:
    - verifies rectangular shape (no row shorter/longer than header)
    - returns list[dict] like DictReader would
    """
    if not path.exists():
        return []
    header, data_rows = _validate_rectangular_csv(path)
    if not header:
        return []

    out: list[dict] = []
    for row in data_rows:
        out.append({header[i]: row[i] for i in range(len(header))})
    return out


def _require_headers(path: pathlib.Path, present_headers: Iterable[str], required_headers: list[str]) -> None:
    present = set(h.strip() for h in present_headers if h is not None)
    missing = [h for h in required_headers if h not in present]
    if missing:
        raise CsvSchemaError(
            f"{path.as_posix()}: missing required header(s): {', '.join(missing)}"
        )


def read_csv(path: pathlib.Path) -> list[dict]:
    """
    Strict read for pending inputs; safe read for canonicals.
    We keep canonicals tolerant (they're created/maintained by scripts),
    but pending files must be strict to protect ingestion.
    """
    # Pending files must be strict
    if "data/pending/" in path.as_posix().replace("\\", "/"):
        return _read_csv_strict_dicts(path)

    # Canonicals / others: still use DictReader for convenience
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: pathlib.Path, rows: list[dict], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in headers})


def ensure_file(path: pathlib.Path, headers: list[str]) -> None:
    if not path.exists():
        write_csv(path, [], headers)


# ----------------------------
# Schema / headers
# ----------------------------

REQ_MASTER = ["date", "location", "event", "participants_on_record", "source_urls", "notes"]
OPT_MASTER = ["deep_search_event", "deep_search_notes"]
ALL_MASTER = REQ_MASTER + OPT_MASTER

REQ_PEOPLE = ["date", "location", "event", "person", "role", "source_urls", "deep_search_person", "deep_search_notes"]

REQ_UNVER_EVENTS = ["date", "location", "event", "primary_source", "secondary_source", "confidence", "notes", "next_step"]
REQ_UNVER_PEOPLE = ["person", "possible_event_date", "location", "alleged_association", "source", "confidence", "notes", "next_step"]
REQ_UNVER_CONN = ["entity_a", "entity_b", "connection_type", "source", "confidence", "notes", "next_step"]

# Pending unverified template should include at least: "type" plus all fields used by any type.
# We only *require* the subset needed for routing and the fields for each type.
REQ_PENDING_UNVERIFIED_MIN = ["type"]


# ----------------------------
# Normalization
# ----------------------------

def normalize_master_row(r: dict) -> dict:
    out = {}
    for k in ALL_MASTER:
        v = (r.get(k, "") or "").strip()
        if k in ("location", "event"):
            v = " ".join(v.split())
        out[k] = v
    if not out.get("deep_search_event"):
        out["deep_search_event"] = "pending"
    return out


def key_master(r: dict) -> tuple:
    return (r.get("date", "").strip(), r.get("location", "").strip(), r.get("event", "").strip())


def parse_date_key(d: str) -> tuple:
    if "–" in d:
        d = d.split("–", 1)[0].strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            dt = datetime.strptime(d, fmt)
            return (0, dt.year, dt.month if fmt != "%Y" else 1, dt.day if fmt == "%Y-%m-%d" else 1, d)
        except ValueError:
            pass
    return (1, 9999, 12, 31, d or "~")


def normalize_people_row(r: dict) -> dict:
    out = {}
    for k in REQ_PEOPLE:
        out[k] = (r.get(k, "") or "").strip()
    if not out.get("deep_search_person"):
        out["deep_search_person"] = "pending"
    return out


def key_people(r: dict) -> tuple:
    return (r.get("date", "").strip(), r.get("location", "").strip(), r.get("event", "").strip(), r.get("person", "").strip())


# ----------------------------
# Merge steps
# ----------------------------

def merge_master(DATA: pathlib.Path) -> list[pathlib.Path]:
    MASTER = DATA / "master" / "master_timeline.csv"
    ensure_file(MASTER, ALL_MASTER)
    master_rows = read_csv(MASTER)

    merged, seen = [], set()
    for r in master_rows:
        for k in OPT_MASTER:
            r.setdefault(k, "")
        nr = normalize_master_row(r)
        k = key_master(nr)
        if k not in seen:
            merged.append(nr)
            seen.add(k)

    pending_dir = DATA / "pending"
    pendings: list[pathlib.Path] = []

    for p in sorted(pending_dir.glob("pending_updates_*.csv")):
        chunk = read_csv(p)
        if not chunk:
            continue

        # Guardrail: required headers for pending_updates_*.csv
        _require_headers(p, chunk[0].keys(), REQ_MASTER)
        # Optional columns allowed; we fill if missing.

        pendings.append(p)
        for r in chunk:
            for k in OPT_MASTER:
                r.setdefault(k, "")
            nr = normalize_master_row(r)
            k = key_master(nr)
            if k not in seen:
                merged.append(nr)
                seen.add(k)

    merged.sort(key=lambda r: (parse_date_key(r["date"]), r["location"].lower(), r["event"].lower()))
    write_csv(MASTER, merged, ALL_MASTER)
    return pendings


def merge_people(DATA: pathlib.Path) -> list[pathlib.Path]:
    PEOPLE = DATA / "master" / "verified_people_events.csv"
    ensure_file(PEOPLE, REQ_PEOPLE)
    existing = read_csv(PEOPLE)

    merged, seen = [], set()
    for r in existing:
        nr = normalize_people_row(r)
        k = key_people(nr)
        if k not in seen:
            merged.append(nr)
            seen.add(k)

    pending_dir = DATA / "pending"
    pendings: list[pathlib.Path] = []

    for p in sorted(pending_dir.glob("pending_people_*.csv")):
        chunk = read_csv(p)
        if not chunk:
            continue

        # Guardrail: required headers for pending_people_*.csv
        _require_headers(p, chunk[0].keys(), REQ_PEOPLE)

        pendings.append(p)
        for r in chunk:
            nr = normalize_people_row(r)
            k = key_people(nr)
            if k not in seen:
                merged.append(nr)
                seen.add(k)

    merged.sort(key=lambda r: (parse_date_key(r["date"]), r["location"].lower(), r["event"].lower(), r["person"].lower()))
    write_csv(PEOPLE, merged, REQ_PEOPLE)
    return pendings


def merge_unverified(DATA: pathlib.Path) -> list[pathlib.Path]:
    UNVER_EVENTS = DATA / "unverified" / "unverified_events.csv"
    UNVER_PEOPLE = DATA / "unverified" / "unverified_people.csv"
    UNVER_CONN = DATA / "unverified" / "unverified_connections.csv"

    ensure_file(UNVER_EVENTS, REQ_UNVER_EVENTS)
    ensure_file(UNVER_PEOPLE, REQ_UNVER_PEOPLE)
    ensure_file(UNVER_CONN, REQ_UNVER_CONN)

    ue = read_csv(UNVER_EVENTS)
    up = read_csv(UNVER_PEOPLE)
    uc = read_csv(UNVER_CONN)

    def dedupe(existing, headers):
        seen_local = set()
        out = []
        for r in existing:
            key = tuple((r.get(h, "") or "").strip() for h in headers)
            if key not in seen_local:
                out.append({h: (r.get(h, "") or "").strip() for h in headers})
                seen_local.add(key)
        return out

    pending_dir = DATA / "pending"
    pendings: list[pathlib.Path] = []

    for p in sorted(pending_dir.glob("pending_unverified_*.csv")):
        rows = read_csv(p)
        if not rows:
            continue

        # Guardrail: must at least contain routing column 'type'
        _require_headers(p, rows[0].keys(), REQ_PENDING_UNVERIFIED_MIN)

        pendings.append(p)
        for r in rows:
            t = (r.get("type", "") or "").strip().lower()

            if t == "event":
                # Guardrail: event rows must contain required event fields
                _require_headers(p, r.keys(), REQ_UNVER_EVENTS)
                ue.append({h: (r.get(h, "") or "").strip() for h in REQ_UNVER_EVENTS})

            elif t == "person":
                _require_headers(p, r.keys(), REQ_UNVER_PEOPLE)
                up.append({h: (r.get(h, "") or "").strip() for h in REQ_UNVER_PEOPLE})

            elif t == "connection":
                _require_headers(p, r.keys(), REQ_UNVER_CONN)
                uc.append({h: (r.get(h, "") or "").strip() for h in REQ_UNVER_CONN})

            else:
                # If blank lines exist, allow them; otherwise fail.
                # (This prevents silent drops of mis-typed "Type" values.)
                if any((v or "").strip() for v in r.values()):
                    raise CsvSchemaError(
                        f"{p.as_posix()}: unknown type='{t}'. Expected one of: event, person, connection."
                    )

    ue = dedupe(ue, REQ_UNVER_EVENTS)
    up = dedupe(up, REQ_UNVER_PEOPLE)
    uc = dedupe(uc, REQ_UNVER_CONN)

    ue.sort(key=lambda r: (r["date"].lower(), r["location"].lower(), r["event"].lower()))
    up.sort(key=lambda r: (r["possible_event_date"].lower(), r["location"].lower(), r["person"].lower()))
    uc.sort(key=lambda r: (r["entity_a"].lower(), r["entity_b"].lower(), r["connection_type"].lower()))

    write_csv(UNVER_EVENTS, ue, REQ_UNVER_EVENTS)
    write_csv(UNVER_PEOPLE, up, REQ_UNVER_PEOPLE)
    write_csv(UNVER_CONN, uc, REQ_UNVER_CONN)

    return pendings


def archive_files(archive_dir: pathlib.Path, files: list[pathlib.Path]) -> None:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    archive_dir.mkdir(parents=True, exist_ok=True)
    for p in files:
        dest = archive_dir / f"{p.stem}.processed_{ts}{p.suffix}"
        p.replace(dest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=".", help="Scope base directory")
    args = ap.parse_args()

    BASE = pathlib.Path(args.base).resolve()
    DATA = BASE / "data"
    ARCHIVE = DATA / "archive"

    try:
        pu = merge_master(DATA)
        pp = merge_people(DATA)
        pu2 = merge_unverified(DATA)
        archive_files(ARCHIVE, pu + pp + pu2)
        print("Merged master + people + unverified successfully.")
    except CsvSchemaError as e:
        # Fail loudly and clearly in CI
        raise SystemExit(f"[import_pending] CSV SCHEMA ERROR: {e}") from e


if __name__ == "__main__":
    main()
