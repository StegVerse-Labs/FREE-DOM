# FREE-DOM Documentation Index

Documentation, policies, and reference diagrams for the FREE-DOM project.

## Policies

- [Ethics & Privacy Policy](ETHICS_AND_PRIVACY_POLICY.md) — handling of sensitive submissions, anonymization rules, and referral protocol.
- [Terms of Access / Use](../TERMS_OF_ACCESS.md) — conditions of use for the repository and its data.
- [Contributing Guide](../CONTRIBUTING.md) — submission standards: factual accuracy, anonymity, reproducibility, and version traceability.

## Architecture & Pipeline

- [DevOps Pipeline (diagram)](FREE_DOM_devops_pipeline.png) — visual overview of the ingestion and validation flow.
- [DevOps Pipeline (ASCII)](FREE_DOM_devops_pipeline.txt) — text version of the pipeline diagram.
- [Repository Diagram (ASCII)](FREE_DOM_repo_diagram.txt) — repository layout map.
- [Token Vault Developer Guide](TV_DEV_GUIDE.md) — TV/TVC secret-rotation integration for CI workflows.

## Data Layer

The canonical data-layer reference lives at [`data/README.md`](../data/README.md). A pointer index is also kept at [`DATA_FOLDER.md`](../DATA_FOLDER.md).

## Badges

Generated automatically by CI and stored in [`docs/badges/`](badges/):

- `version.svg` — current semantic version (from `data/summary/VERSION`), built by `scripts/make_version_badge.py`.
- `freshness.svg` — most recent AI Search Agent sweep date, built by `scripts/make_freshness_badge.py`.

## Workflows

|Workflow       |File                                   |Purpose                                                                                    |
|---------------|---------------------------------------|-------------------------------------------------------------------------------------------|
|AI Search Agent|`.github/workflows/ai_search_agent.yml`|Daily public-source (RSS/news) OSINT sweep; appends leads and rebuilds summaries.          |
|Auto Update    |`.github/workflows/auto_update.yml`    |Merges pending data into master, rebuilds checklist/changelog/badges, validates CSV schema.|

See the project [README](../README.md) for the full overview.