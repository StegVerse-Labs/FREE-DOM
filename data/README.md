# FREE-DOM Data Layer

This directory contains all structured datasets, ingestion inputs, automation outputs, and archival history for the FREE-DOM project.

The data layer is intentionally isolated from documentation and scripts to ensure:
- deterministic ingestion,
- clean audit trails,
- reproducible builds,
- clear promotion boundaries (pending → verified),
- and bot-safe operation.

---
# Data Folder Overview

This directory houses all structured datasets, pending leads, and AI-agent outputs for the FREE-DOM project.

The data layer is intentionally separated from documentation and scripts to keep ingestion deterministic, auditable, and bot-safe.

## Structure

| Subfolder | Contents | Description |
|---|---|---|
| `master/` | `master_timeline.csv`, `verified_people_events.csv` | Canonical, validated datasets used for downstream outputs |
| `pending/` | `pending_updates_*.csv`, `pending_people_*.csv`, `pending_unverified_*.csv` (and/or optional subfolders) | New incoming data awaiting merge and review |
| `unverified/` | `unverified_events.csv`, `unverified_people.csv`, `unverified_connections.csv` | Leads and associations that are **not yet verified** |
| `sources/` | `sources_whitelist.csv` | Approved public RSS/news feeds monitored by the AI agent |
| `logs/ai_agent/` | `agent_run_*.jsonl` | Raw machine logs from each public-source scan |
| `summary/` | `ai_agent_summary.csv`, `ai_agent_sources_index.csv`, `VERSION`, `CHANGELOG_batches.csv` | Aggregated metrics, coverage dashboards, and version artifacts |
| `archive/` | `*.processed_*.csv` | Timestamped snapshots of processed pending imports for audit traceability |

> Note on `pending/` layout:  
> Some repos keep pending files directly in `data/pending/`. Others optionally group them under `data/pending/events/`, `data/pending/people/`, `data/pending/unverified/`.  
> **Scripts must match the chosen layout.** If you use subfolders, update `scripts/import_pending.py` glob paths accordingly.

## How It Works (High-Level)

1. **New items enter as pending**  
   Drop CSV batches into `data/pending/` (or its configured subfolders).

2. **Auto Update merges pending into tracked datasets**  
   The Auto Update workflow ingests pending batches, updates canonical CSVs, and archives processed inputs to `data/archive/`.

3. **AI Search Agent enriches with public-source leads (non-destructive)**  
   The agent scans whitelisted public sources and appends links/notes to relevant rows while logging runs under `data/logs/ai_agent/`.  
   **It does not auto-verify or auto-promote claims.**

4. **Verification is a promotion step (intentional, reviewable)**  
   Items move from `unverified/` to `master/` only when verification thresholds are met (policy + review), preserving an auditable trail.

## Governance Notes

- Public OSINT only: no private, paywalled-circumvention, or non-public sources.
- `unverified/` is explicitly non-validated.
- `master/` is treated as canonical and should remain reproducible.
- Automation is designed to be idempotent (safe to rerun).

---

---
## 📂 Directory Structure

```
data/
master/              ← Canonical verified datasets
pending/             ← New or partially verified submissions
unverified/          ← Leads and unconfirmed information
sources/             ← RSS/news feeds monitored by the AI Search Agent
logs/ai_agent/       ← Raw JSONL logs of agent sweeps
summary/             ← Aggregated dashboards, source indexes, VERSION
archive/             ← Processed import snapshots for audit traceability
```

No data-bearing CSV files should exist at repository root.

---

## 🧩 Folder Roles

### `master/`
Contains fully verified, structured datasets:
- `master_timeline.csv`
- `verified_people_events.csv`
- any canonical registries

These files are modified only via automation.

Managed by: **Auto Update workflow**

---

### `pending/`
Holds new data awaiting merge:
- `pending_updates_*.csv`
- `pending_people_*.csv`
- `pending_unverified_*.csv`

These are processed automatically and then moved to `archive/`.

Managed by: **Human review + Auto Update workflow**

---

### `unverified/`
Stores leads requiring further confirmation:
- `unverified_events.csv`
- `unverified_people.csv`
- `unverified_connections.csv`

Entries here are not considered verified facts.

Managed by: **Auto Update workflow**

---

### `sources/`
Contains:
- `sources_whitelist.csv`

This file defines public RSS/news feeds monitored by the AI Search Agent.

Only publicly accessible sources are allowed.

Managed manually.

---

### `logs/ai_agent/`
Raw `.jsonl` logs from AI Search Agent runs.
Provides full transparency into:
- keywords used
- links discovered
- source domains
- timestamps

Logs are append-only.

Managed by: **AI Search Agent workflow**

---

### `summary/`
Automatically generated artifacts:
- `ai_agent_summary.csv`
- `ai_agent_sources_index.csv`
- `CHANGELOG_batches.csv`
- `VERSION`

This directory represents the operational dashboard layer.

Managed by: **AI Search Agent + Auto Update workflows**

---

### `archive/`
Processed pending imports are moved here with timestamped filenames.

This preserves:
- historical state
- import traceability
- audit history

Managed by: **Auto Update workflow**

---

## ⚙️ Automation Overview

### AI Search Agent
- Runs daily
- Scans whitelisted public sources
- Appends leads (non-destructively)
- Generates summaries

Script: `scripts/search_agent.py`

---

### Auto Update
- Merges pending datasets into master
- Regenerates CHECKLIST.md
- Rebuilds CHANGELOG.md
- Validates CSV schema
- Archives processed batches

Scripts:
- `import_pending.py`
- `build_checklist.py`
- `build_changelog.py`
- `update_timeline.py`

---

## 🔐 Governance Notes

- No sensitive personal testimony is stored in this directory.
- No private or non-public sources are ingested.
- Unverified data remains segregated.
- Promotion to `master/` requires structured validation.
- All automation is idempotent and safe to rerun.

---

## 🧱 Design Principles

This data layer is built to be:

- Bot-operable
- Deterministic
- Audit-friendly
- Non-destructive
- Public-source only
- Structurally consistent across StegVerse repositories

It is the canonical ingestion backbone of FREE-DOM.

---

_Last updated automatically via CI workflows._
