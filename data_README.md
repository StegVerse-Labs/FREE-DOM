# Data Folder Reference

The canonical documentation for the FREE-DOM data layer lives at:

- `data/README.md`

This file exists only as an index pointer to reduce duplication and prevent documentation drift.

## Quick Summary

All structured datasets, ingestion inputs, automation outputs, logs, summaries, and archives are stored under:

- `data/`

Primary subfolders:

- `data/master/` — canonical verified datasets
- `data/pending/` — incoming batches awaiting merge/review
- `data/unverified/` — leads not yet verified
- `data/sources/` — approved public-source whitelist (RSS/news)
- `data/logs/ai_agent/` — raw JSONL logs from agent sweeps
- `data/summary/` — dashboards, versioning, coverage metrics
- `data/archive/` — timestamped processed batches for audit history
