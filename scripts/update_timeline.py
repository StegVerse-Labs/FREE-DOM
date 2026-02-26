#!/usr/bin/env python3
import argparse, sys, csv, pathlib
from datetime import datetime

def read_csv(path: pathlib.Path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def check_headers(rows, required, name):
    if not rows:
        return
    missing = [h for h in required if h not in rows[0].keys()]
    if missing:
        print(f"::error ::{name} missing headers: {missing}")
        sys.exit(1)

def check_dates(rows, field, name):
    for i, r in enumerate(rows, start=2):
        val = (r.get(field,"") or "").strip()
        if not val:
            print(f"::warning ::{name} row {i} has empty {field}")
            continue
        if "–" in val:
            val = val.split("–",1)[0].strip()
        ok = False
        for fmt in ("%Y-%m-%d","%Y-%m","%Y"):
            try:
                datetime.strptime(val, fmt)
                ok = True
                break
            except ValueError:
                pass
        if not ok:
            raw = (r.get(field,"") or "").strip()
            print(f"::warning ::{name} row {i} has non-standard date '{raw}'")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=".", help="Scope base directory")
    args = ap.parse_args()

    base = pathlib.Path(args.base).resolve()
    data_dir = base / "data"

    master_path = data_dir / "master" / "master_timeline.csv"
    people_path = data_dir / "master" / "verified_people_events.csv"

    master_headers = [
        "date","location","event","participants_on_record","source_urls","notes",
        "deep_search_event","deep_search_notes"
    ]
    people_headers = [
        "date","location","event","person","role","source_urls","deep_search_person","deep_search_notes"
    ]

    mt = read_csv(master_path)
    check_headers(mt, master_headers, str(master_path))
    check_dates(mt, "date", str(master_path))

    pe = read_csv(people_path)
    check_headers(pe, people_headers, str(people_path))
    check_dates(pe, "date", str(people_path))

    # Unverified (tolerant if empty)
    ue_path = data_dir / "unverified" / "unverified_events.csv"
    up_path = data_dir / "unverified" / "unverified_people.csv"
    uc_path = data_dir / "unverified" / "unverified_connections.csv"

    ue = read_csv(ue_path)
    if ue:
        ueh = ["date","location","event","primary_source","secondary_source","confidence","notes","next_step"]
        check_headers(ue, ueh, str(ue_path))
        check_dates(ue, "date", str(ue_path))

    up = read_csv(up_path)
    if up:
        uph = ["person","possible_event_date","location","alleged_association","source","confidence","notes","next_step"]
        check_headers(up, uph, str(up_path))

    uc = read_csv(uc_path)
    if uc:
        uch = ["entity_a","entity_b","connection_type","source","confidence","notes","next_step"]
        check_headers(uc, uch, str(uc_path))

    print(f"[{base}] master_timeline rows: {len(mt)}")
    print(f"[{base}] verified_people_events rows: {len(pe)}")
    print(f"[{base}] unverified_events rows: {len(ue)}")
    print(f"[{base}] unverified_people rows: {len(up)}")
    print(f"[{base}] unverified_connections rows: {len(uc)}")

if __name__ == "__main__":
    main()
