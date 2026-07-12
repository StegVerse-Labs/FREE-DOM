#!/usr/bin/env python3
"""Governed pending-record importer.

Pending inputs are validated by default. Canonical mutation and archival occur only
when the operator supplies --allow-master-promotion. Files whose names contain
"template" are never treated as ingestible batches.
"""
from __future__ import annotations

import argparse
import csv
import pathlib
from datetime import datetime, timezone
from typing import Iterable


class CsvSchemaError(RuntimeError):
    pass


REQ_MASTER = ["date", "location", "event", "participants_on_record", "source_urls", "notes"]
OPT_MASTER = ["deep_search_event", "deep_search_notes"]
ALL_MASTER = REQ_MASTER + OPT_MASTER
REQ_PEOPLE = ["date", "location", "event", "person", "role", "source_urls", "deep_search_person", "deep_search_notes"]
REQ_UNVER_EVENTS = ["date", "location", "event", "primary_source", "secondary_source", "confidence", "notes", "next_step"]
REQ_UNVER_PEOPLE = ["person", "possible_event_date", "location", "alleged_association", "source", "confidence", "notes", "next_step"]
REQ_UNVER_CONN = ["entity_a", "entity_b", "connection_type", "source", "confidence", "notes", "next_step"]


def is_template(path: pathlib.Path) -> bool:
    return "template" in path.stem.lower()


def pending_files(directory: pathlib.Path, pattern: str) -> list[pathlib.Path]:
    return [path for path in sorted(directory.glob(pattern)) if not is_template(path)]


def read_rows(path: pathlib.Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8") as handle:
        raw = list(csv.reader(handle))
    if not raw:
        return [], []
    header = raw[0]
    if not header or any(not value.strip() for value in header):
        raise CsvSchemaError(f"{path.as_posix()}: empty header name")
    width = len(header)
    rows: list[dict[str, str]] = []
    for line_number, row in enumerate(raw[1:], start=2):
        if len(row) != width:
            raise CsvSchemaError(
                f"{path.as_posix()}: row {line_number} has {len(row)} columns; expected {width}"
            )
        rows.append({header[index]: row[index] for index in range(width)})
    return header, rows


def require_headers(path: pathlib.Path, headers: Iterable[str], required: Iterable[str]) -> None:
    present = {value.strip() for value in headers}
    missing = [value for value in required if value not in present]
    if missing:
        raise CsvSchemaError(f"{path.as_posix()}: missing required headers: {', '.join(missing)}")


def read_dicts(path: pathlib.Path) -> list[dict[str, str]]:
    _, rows = read_rows(path)
    return rows


def write_dicts(path: pathlib.Path, rows: list[dict[str, str]], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def ensure_file(path: pathlib.Path, headers: list[str]) -> None:
    if not path.exists():
        write_dicts(path, [], headers)


def normalize(row: dict[str, str], headers: list[str]) -> dict[str, str]:
    return {header: " ".join((row.get(header, "") or "").strip().split()) for header in headers}


def parse_date(value: str) -> tuple:
    value = value.split("–", 1)[0].strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            parsed = datetime.strptime(value, fmt)
            return (0, parsed.year, parsed.month, parsed.day, value)
        except ValueError:
            continue
    return (1, 9999, 12, 31, value or "~")


def dedupe(rows: list[dict[str, str]], headers: list[str]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    seen: set[tuple[str, ...]] = set()
    for row in rows:
        normalized = normalize(row, headers)
        key = tuple(normalized[header] for header in headers)
        if key not in seen:
            output.append(normalized)
            seen.add(key)
    return output


def validate_pending(data: pathlib.Path) -> list[pathlib.Path]:
    pending = data / "pending"
    accepted: list[pathlib.Path] = []

    for path in pending_files(pending, "pending_updates_*.csv"):
        headers, rows = read_rows(path)
        require_headers(path, headers, REQ_MASTER)
        if rows:
            accepted.append(path)

    for path in pending_files(pending, "pending_people_*.csv"):
        headers, rows = read_rows(path)
        require_headers(path, headers, REQ_PEOPLE)
        if rows:
            accepted.append(path)

    for path in pending_files(pending, "pending_unverified_*.csv"):
        headers, rows = read_rows(path)
        require_headers(path, headers, ["type"])
        for row in rows:
            kind = (row.get("type", "") or "").strip().lower()
            if kind == "event":
                require_headers(path, headers, REQ_UNVER_EVENTS)
            elif kind == "person":
                require_headers(path, headers, REQ_UNVER_PEOPLE)
            elif kind == "connection":
                require_headers(path, headers, REQ_UNVER_CONN)
            elif any((value or "").strip() for value in row.values()):
                raise CsvSchemaError(f"{path.as_posix()}: unknown type {kind!r}")
        if rows:
            accepted.append(path)

    return accepted


def merge_master(data: pathlib.Path) -> list[pathlib.Path]:
    destination = data / "master" / "master_timeline.csv"
    ensure_file(destination, ALL_MASTER)
    rows = read_dicts(destination)
    inputs = pending_files(data / "pending", "pending_updates_*.csv")
    for path in inputs:
        _, chunk = read_rows(path)
        for row in chunk:
            normalized = normalize(row, ALL_MASTER)
            normalized["deep_search_event"] = normalized["deep_search_event"] or "pending"
            rows.append(normalized)
    rows = dedupe(rows, ALL_MASTER)
    rows.sort(key=lambda row: (parse_date(row["date"]), row["location"].lower(), row["event"].lower()))
    write_dicts(destination, rows, ALL_MASTER)
    return inputs


def merge_people(data: pathlib.Path) -> list[pathlib.Path]:
    destination = data / "master" / "verified_people_events.csv"
    ensure_file(destination, REQ_PEOPLE)
    rows = read_dicts(destination)
    inputs = pending_files(data / "pending", "pending_people_*.csv")
    for path in inputs:
        _, chunk = read_rows(path)
        for row in chunk:
            normalized = normalize(row, REQ_PEOPLE)
            normalized["deep_search_person"] = normalized["deep_search_person"] or "pending"
            rows.append(normalized)
    rows = dedupe(rows, REQ_PEOPLE)
    rows.sort(key=lambda row: (parse_date(row["date"]), row["location"].lower(), row["event"].lower(), row["person"].lower()))
    write_dicts(destination, rows, REQ_PEOPLE)
    return inputs


def merge_unverified(data: pathlib.Path) -> list[pathlib.Path]:
    event_path = data / "unverified" / "unverified_events.csv"
    people_path = data / "unverified" / "unverified_people.csv"
    connection_path = data / "unverified" / "unverified_connections.csv"
    ensure_file(event_path, REQ_UNVER_EVENTS)
    ensure_file(people_path, REQ_UNVER_PEOPLE)
    ensure_file(connection_path, REQ_UNVER_CONN)
    events = read_dicts(event_path)
    people = read_dicts(people_path)
    connections = read_dicts(connection_path)
    inputs = pending_files(data / "pending", "pending_unverified_*.csv")
    for path in inputs:
        _, rows = read_rows(path)
        for row in rows:
            kind = (row.get("type", "") or "").strip().lower()
            if kind == "event":
                events.append(normalize(row, REQ_UNVER_EVENTS))
            elif kind == "person":
                people.append(normalize(row, REQ_UNVER_PEOPLE))
            elif kind == "connection":
                connections.append(normalize(row, REQ_UNVER_CONN))
    events = dedupe(events, REQ_UNVER_EVENTS)
    people = dedupe(people, REQ_UNVER_PEOPLE)
    connections = dedupe(connections, REQ_UNVER_CONN)
    write_dicts(event_path, events, REQ_UNVER_EVENTS)
    write_dicts(people_path, people, REQ_UNVER_PEOPLE)
    write_dicts(connection_path, connections, REQ_UNVER_CONN)
    return inputs


def archive_files(directory: pathlib.Path, files: list[pathlib.Path]) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory.mkdir(parents=True, exist_ok=True)
    for path in files:
        if is_template(path):
            raise CsvSchemaError(f"refusing to archive template input: {path.as_posix()}")
        path.replace(directory / f"{path.stem}.processed_{timestamp}{path.suffix}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=".", help="Repository root")
    parser.add_argument(
        "--allow-master-promotion",
        action="store_true",
        help="Explicitly authorize pending-to-canonical mutation for this invocation",
    )
    args = parser.parse_args()
    data = pathlib.Path(args.base).resolve() / "data"

    try:
        accepted = validate_pending(data)
        print(f"Validated {len(accepted)} non-template pending batch(es).")
        if not args.allow_master_promotion:
            print("DENY promotion_authority_missing; validation completed without mutation.")
            return 0
        files = merge_master(data) + merge_people(data) + merge_unverified(data)
        archive_files(data / "archive", files)
        print("ALLOW explicit_pending_promotion_completed")
        return 0
    except CsvSchemaError as exc:
        raise SystemExit(f"[import_pending] CSV SCHEMA ERROR: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
