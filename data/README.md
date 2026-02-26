# FREE-DOM Data Layer

This directory contains all structured datasets, ingestion inputs, automation outputs, and archival history for the FREE-DOM project.

The data layer is intentionally isolated from documentation and scripts to ensure:

- deterministic ingestion  
- clean audit trails  
- reproducible builds  
- clear promotion boundaries (pending → verified)  
- bot-safe operation  

---

## 📂 Directory Structure
```
data/
master/              ← Canonical verified datasets
pending/             ← Incoming CSV batches awaiting merge
unverified/          ← Leads not yet verified
sources/             ← Approved public RSS/news feeds
logs/ai_agent/       ← Raw JSONL logs from agent sweeps
summary/             ← Dashboards, metrics, VERSION, changelog batches
archive/             ← Timestamped processed imports for audit traceability
```

No data-bearing CSV files should exist at repository root.

---

## 🧩 Folder Roles

### `master/`
Contains validated datasets such as:

- `master_timeline.csv`
- `verified_people_events.csv`

These represent canonical structured data.  
Modified only via automation.

Managed by: **Auto Update workflow**

---

### `pending/`
Holds new CSV batches:

- `pending_updates_*.csv`
- `pending_people_*.csv`
- `pending_unverified_*.csv`

Processed automatically and then archived.

Managed by: **Human review + Auto Update workflow**

---

### `unverified/`
Tracks unconfirmed information:

- `unverified_events.csv`
- `unverified_people.csv`
- `unverified_connections.csv`

Entries here are not treated as verified facts.

Managed by: **Auto Update workflow**

---

### `sources/`
Contains:

- `sources_whitelist.csv`

Defines publicly accessible RSS/news feeds monitored by the AI Search Agent.

Managed manually.

---

### `logs/ai_agent/`
Raw `.jsonl` logs of agent runs.  
Provides transparency into:

- keywords used  
- links discovered  
- source domains  
- timestamps  

Append-only.

Managed by: **AI Search Agent workflow**

---

### `summary/`
Automatically generated artifacts:

- `ai_agent_summary.csv`
- `ai_agent_sources_index.csv`
- `CHANGELOG_batches.csv`
- `VERSION`

Represents the operational dashboard layer.

Managed by: **AI Search Agent + Auto Update workflows**

---

### `archive/`
Processed pending imports are moved here with timestamped filenames.

Preserves:

- historical state  
- import traceability  
- audit history  

Managed by: **Auto Update workflow**

---

## ⚙️ Automation Overview

### AI Search Agent
- Runs on schedule
- Scans approved public sources
- Appends non-destructive leads
- Generates coverage summaries

Script: `scripts/search_agent.py`

---

### Auto Update
- Merges pending batches into master
- Rebuilds CHECKLIST.md
- Updates CHANGELOG.md
- Validates schema
- Archives processed imports

Scripts:
- `import_pending.py`
- `build_checklist.py`
- `build_changelog.py`
- `update_timeline.py`

---

## 🔐 Governance Principles

- Public OSINT sources only  
- No private or non-public ingestion  
- Unverified data remains segregated  
- Promotion to `master/` is intentional and reviewable  
- Automation is idempotent and safe to rerun  

---

This directory is the canonical ingestion backbone of FREE-DOM.
