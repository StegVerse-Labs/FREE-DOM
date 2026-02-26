# FREE-DOM: Factually Recounting Epstein’s Era — Deconstruction of Morality

![Version](docs/badges/version.svg)

![Freshness](docs/badges/freshness.svg)

A public, evidence-first research repository designed to support fiction authors and investigative journalists by maintaining **structured, factual timelines** of publicly verifiable events, court dockets, and related data.

---

## 📘 Table of Contents
- [Workflow Status](#-workflow-status)
- [Repository Layout](#-repository-layout)
- [Workflows Overview](#️-workflows-overview)
- [Purpose](#-purpose)
- [Sensitive Information Protocol](#-sensitive-information-protocol)
- [Documentation & Policies](#-documentation--policies)
- [Data Folder Reference](#-data-folder-reference)
- [Contributing](#-contributing)
- [Repository Live Status](#-repository-live-status)

---

## 🧩 Workflow Status

| Workflow | Status | Description |
|-----------|---------|--------------|
| **AI Search Agent** | [![AI Search Agent](https://github.com/StegVerse/FREE-DOM/actions/workflows/ai_search_agent.yml/badge.svg)](https://github.com/StegVerse/FREE-DOM/actions/workflows/ai_search_agent.yml) | Runs daily OSINT sweeps from whitelisted sources and updates leads + summaries. |
| **Auto Update** | [![Auto Update](https://github.com/StegVerse/FREE-DOM/actions/workflows/auto_update.yml/badge.svg)](https://github.com/StegVerse/FREE-DOM/actions/workflows/auto_update.yml) | Merges pending datasets into master, rebuilds checklist/changelog, and validates schema. |

---

## 📂 Repository Layout

```
data/
  master/              ← Canonical verified datasets
  pending/             ← New or partially verified submissions
  unverified/          ← Leads and unconfirmed information
  sources/             ← RSS/news feeds monitored by the AI Search Agent
  logs/ai_agent/       ← Raw JSONL logs of agent sweeps
  summary/             ← Aggregated hit summaries and source indexes
  archive/             ← Processed import snapshots for audit
scripts/               ← Automation scripts and utilities
.github/workflows/     ← CI/CD for ingestion and validation
docs/                  ← Diagrams, ASCII maps, badges, and policies
```

---

## ⚙️ Workflows Overview

- **AI Search Agent** – performs daily public-source sweeps (RSS/news only) and appends leads to records.  
- **Auto Update** – merges pending data into master, updates [CHECKLIST.md](CHECKLIST.md) and [CHANGELOG.md](CHANGELOG.md), and validates schema.  
- **Validation Layer** – ensures CSV consistency and master integrity.

---

## 🧠 Purpose

FREE-DOM exists to preserve factual record-keeping while empowering creative, educational, and investigative work **without directly naming real individuals** in narrative form.  
It keeps transparency high, maintains auditability, and prevents misinformation.

---

## 🔒 Sensitive Information Protocol
Submissions containing identifying details, personal testimony, or allegations are handled under strict privacy rules:

1. **Review & Secure Storage:** Such submissions are **not** placed in the public repo. They are reviewed and stored in an encrypted location.  
2. **Possible Referral:** Credible allegations of criminal activity **may be referred** to relevant authorities or qualified journalists.  
3. **Public Integration (Anonymized):** We will include **only** non-identifying details (dates, locations, public sources) that meet our policies.

See the full [Ethics & Privacy Policy](docs/ETHICS_AND_PRIVACY_POLICY.md).

---

## 📄 Documentation & Policies
- **Ethics & Privacy Policy:** [docs/ETHICS_AND_PRIVACY_POLICY.md](docs/ETHICS_AND_PRIVACY_POLICY.md)  
- **Terms of Access / Use:** [TERMS_OF_ACCESS.md](TERMS_OF_ACCESS.md)  
- **Documentation Index:** [docs/README.md](docs/README.md)

---

## 🧩 Data Folder Reference

| Folder | Purpose | Managed By |
|--------|--------|------------|
| `data/master/` | Verified datasets | Auto Update |
| `data/pending/` | New entries awaiting merge | Human + Auto Update |
| `data/unverified/` | Leads needing confirmation | Auto Update |
| `data/sources/` | RSS/news feeds | Manual |
| `data/logs/ai_agent/` | Raw agent logs | AI Search Agent |
| `data/summary/` | Aggregated dashboards & VERSION | AI Search Agent / Auto Update |
| `data/archive/` | Processed batch history | Auto Update |

---

## 🧱 Contributing
Please read the [CONTRIBUTING.md](CONTRIBUTING.md) file before submitting updates.  
All contributions should respect:
- factual accuracy (publicly verifiable sources only),
- anonymity and non-implication of real individuals,
- reproducibility and version traceability,
- compliance with the [Ethics & Privacy Policy](docs/ETHICS_AND_PRIVACY_POLICY.md).

---

## 📊 Repository Live Status

| Metric | Source | Current Value |
|--------|--------|----------------|
| **Version** | `data/summary/VERSION` | _auto-updated by CI_ |
| **Data Freshness (AI Search Agent)** | `data/summary/ai_agent_summary.csv` | _auto-updated_ |
| **Workflow Sync (Auto Update)** | GitHub Actions | 🟢 Passing |
| **Files Verified** | [CHECKLIST.md](CHECKLIST.md) | _auto-count_ |
| **New Leads Pending Review** | `data/unverified/` | _auto-count_ |

_Last sync performed automatically via scheduled GitHub Action._

---

© FREE-DOM Project — a StegVerse initiative for truth, structure, and awareness.
