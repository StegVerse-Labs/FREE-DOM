# FREE-DOM Mirror Handoff

## Source of truth

This is the current repository-local handoff for `StegVerse-Labs/FREE-DOM`.

## Purpose and boundaries

```text
Role: public evidence-first research and structured chronology
Canonical records: data/master/
Unverified leads: data/unverified/
Governed evidence: data/evidence/
Run logs: data/logs/ai_agent/
Derived summaries: data/summary/

Discovery is not verification.
Automation may not promote or persist changes into data/master/.
Cross-repository mutation, release, deployment, tagging, and record promotion are not authorized by this handoff.
```

## Current state

```text
MIRROR_HANDOFF_PRESENT
AI_SEARCH_RUNTIME_BOUND_INSTALLED
AI_SEARCH_CANONICAL_IMMUTABILITY_GATE_INSTALLED
TV_DEPENDENCY_REMOVED_FROM_LOCAL_VALIDATION
AUTO_UPDATE_MASTER_PROMOTION_REMOVED
LOCAL_VALIDATION_RUNTIME_BOUND_INSTALLED
AI_SEARCH_VERIFICATION_PENDING
LOCAL_VALIDATION_VERIFICATION_PENDING
CURRENT_MAIN_VERIFICATION_PENDING
```

## Latest handled events

### AI Search Agent runtime failure

```text
Run ID: 29176837511
Commit: e875c82
Job: sweep
Result: failed after 4 hours, 5 minutes, 1 second
Repair: add timeout-minutes: 30
Repair commit: 1e25e3335bf9e12edba5b020a41169aa5867f69d
Verification: pending
```

### AI Search Agent canonical-write risk

```text
Finding: discovered links could modify canonical notes in the workflow workspace.
Repair: remove data/master/ from the commit surface, restore canonical files, and assert a clean canonical diff.
Repair commit: 38e15acaa90ac7b0adc0c8d21e5e7e1c66502d6b
Preserved commit surface: data/unverified/, data/logs/ai_agent/, data/summary/, data/evidence/
Verification: pending
```

### Auto Update failure and authority repair

```text
Notification: 2026-07-12T14:41:27-05:00
Workflow: Auto Update (with TV)
Run ID: 29206257940
Commit: 38e15acaa90ac7b0adc0c8d21e5e7e1c66502d6b
Job: build
First failing step: Fetch short-lived secrets from TV
Failure: https://StegVerse-Labs/TV was treated as a network endpoint and failed DNS resolution.
Additional risk: the workflow invoked pending-record merge scripts and included data/master/** in its automatic commit surface.
Repair: convert the workflow to governed repository-local validation; remove TV access, id-token permission, pending-record merge, timeline update, and data/master/** commit handling; add a 15-minute timeout and canonical immutability assertion.
Repair commit: f70b502ebef36720c1ae148cb0189d1a02ac1700
Verification: pending
```

## Completion conditions

```text
All workflow YAML parses.
Repository-local tests pass.
AI Search Agent finishes within 30 minutes.
Governed local validation finishes within 15 minutes.
data/master/ remains unchanged in both workflows.
Governed evidence outputs retain source, uncertainty, and non-implication fields.
Passing run IDs, output commit, and artifact paths are recorded here.
```

## Next task

```text
1. Verify Auto Update (Governed Local Validation) on f70b502ebef36720c1ae148cb0189d1a02ac1700 or later.
2. Verify AI Search Agent on 38e15acaa90ac7b0adc0c8d21e5e7e1c66502d6b or later.
3. Inspect logs and annotations for any failure.
4. Confirm data/master/ is unchanged.
5. Record governed evidence manifest, receipt, Merkle batch, log, summary, output commit, and passing run IDs.
```

## Known remaining files

```text
scripts/search_agent.py
  Refactor so canonical DataFrames are never mutated even transiently.

.github/workflows/ai_search_agent.yml
  Verify bounded successful run and governed evidence commit.

.github/workflows/auto_update_tv_patch.yml
  Verify successful local-only run with no canonical mutation.

FREE_DOM_MIRROR_HANDOFF.md
  Record final verification evidence.
```

## Archive readiness

This file contains the exact continuation state; earlier conversation context is not required.
