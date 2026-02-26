# FREE-DOM Data Layer (`/data`)

This directory contains all structured datasets, ingestion inputs, automation outputs, and archival history for the FREE-DOM project.

The data layer is intentionally separated from documentation and scripts to keep ingestion:
- deterministic,
- auditable,
- reproducible,
- and bot-safe.

## Canonical Structure
```
data/
master/        # canonical, verified datasets
pending/       # incoming batches awaiting merge
unverified/    # leads / associations not yet verified
sources/       # whitelisted public RSS/news feeds
logs/          # AI agent run logs (append-only)
summary/       # dashboards + VERSION + batch history
archive/       # processed pending snapshots (audit trail)
```

> **Rule:** No data-bearing CSV files should live at repository root.  
> **Rule:** `data/` root should only contain subfolders + this README.

## Folder Roles

### `master/` (canonical)
Verified datasets used for downstream outputs (edited only through automation):
- `master_timeline.csv`
- `verified_people_events.csv`
- optional canonical registries (e.g., `organizations.csv`, `photo_video_anchors.csv`)

Managed by: **Auto Update**

### `pending/` (inputs)
Incoming batch files to be merged:
- `pending_updates_*.csv`
- `pending_people_*.csv`
- `pending_unverified_*.csv`

Managed by: **Human + Auto Update**  
After processing, batches are moved into `archive/`.

### `unverified/` (leads)
Leads needing confirmation:
- `unverified_events.csv`
- `unverified_people.csv`
- `unverified_connections.csv`

Managed by: **Auto Update** (non-destructive)

### `sources/` (public whitelist)
- `sources_whitelist.csv` — approved public RSS/news feeds

Managed by: **Manual**

### `logs/` (append-only)
AI agent logs (e.g., `logs/ai_agent/agent_run_*.jsonl`) for transparency and audit.

Managed by: **AI Search Agent**

### `summary/` (dashboards)
Generated artifacts used as “ops dashboards,” commonly:
- `ai_agent_summary.csv`
- `ai_agent_sources_index.csv`
- `VERSION`
- `CHANGELOG_batches.csv` (or similar batch history)

Managed by: **AI Search Agent + Auto Update**

### `archive/` (processed snapshots)
Timestamped “processed batch” files preserved for audit traceability.

Managed by: **Auto Update**

## High-Level Flow

1. Drop new batches into `data/pending/`
2. Auto Update merges into `data/master/` and updates checklists/changelog
3. AI Search Agent scans whitelisted public sources and writes logs + summaries
4. Items only “promote” from `unverified/` → `master/` via explicit verification

## Governance Notes

- Public OSINT only (no private or non-public sources)
- `unverified/` is explicitly non-canonical
- `master/` is canonical and should remain reproducible
- Automation should be idempotent (safe to re-run)

_Last updated via repo governance._
