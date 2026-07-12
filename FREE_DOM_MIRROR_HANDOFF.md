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
Templates are scaffolding and may not be ingested, promoted, or archived as real records.
Cross-repository mutation, release, deployment, tagging, and record promotion are not authorized by this handoff.
```

## Current state

```text
MIRROR_HANDOFF_PRESENT
AI_SEARCH_RUNTIME_BOUND_INSTALLED
AI_SEARCH_CANONICAL_IMMUTABILITY_GATE_INSTALLED
TV_DEPENDENCY_REMOVED_FROM_LOCAL_VALIDATION
PRIMARY_AUTO_UPDATE_MASTER_PROMOTION_REMOVED
LOCAL_VALIDATION_RUNTIME_BOUND_INSTALLED
PENDING_IMPORT_DEFAULT_DENY_INSTALLED
PENDING_TEMPLATE_EXCLUSION_INSTALLED
PENDING_IMPORT_GOVERNANCE_TEST_INSTALLED
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

### TV workflow failure

```text
Run ID: 29206257940
Commit: 38e15acaa90ac7b0adc0c8d21e5e7e1c66502d6b
First failing step: Fetch short-lived secrets from TV
Failure: invalid repository-like value used as a network endpoint
Repair commit: f70b502ebef36720c1ae148cb0189d1a02ac1700
Result: TV access, id-token permission, pending merge, timeline mutation, and data/master commit handling removed from that workflow.
```

### Primary auto-update authority gap

```text
Output commit: 15f8382befb6f034fa85302e3543bb8c153186b0
Run ID recorded by output: 29206534584
Finding: .github/workflows/auto_update.yml remained active and still called import_pending.py, update_timeline.py, and committed data/master/ and data/archive/.
Observed effect: three example template files were archived as processed records.
Repair commit: 32cc4c0cf4ddb968eccfb7c7ff2de8c6c3d00fff
Cleanup commits: f07c57c1c07f3a0fb44d6c6c6f78176584f939e9, fea895ecf741baf9724619d7d9c40d4c87b23a2e, c6b28f3db331ee1ad0f3d3ca1adc567ff0693339
Result: primary workflow converted to governed local validation; canonical and archive commit surfaces removed.
```

### Pending importer hardening

```text
Importer repair: d20bb2cf79338301930f145ae136677077184739
Behavior: validation-only by default; canonical mutation requires --allow-master-promotion.
Behavior: filenames containing template are excluded from ingestible pending batches.
Test added: scripts/test_import_pending_governance.py
Test commit: 5e884d9ea911ca160c8330429152563559093c6c
Workflow enforcement commit: c00f7d5d135552d72d50b5f0af7c0522c895c662
Verification: pending GitHub Actions result.
```

## Completion conditions

```text
All workflow YAML parses.
Repository-local tests pass.
AI Search Agent finishes within 30 minutes.
Governed local validation finishes within 15 minutes.
Pending-import governance test passes.
data/master/ remains unchanged in automated workflows.
Template files remain scaffolding and are not processed as records.
Governed evidence outputs retain source, uncertainty, and non-implication fields.
Passing run IDs, output commit, and artifact paths are recorded here.
```

## Next task

```text
1. Verify Governed Local Validation on c00f7d5d135552d72d50b5f0af7c0522c895c662 or later.
2. Verify AI Search Agent on 38e15acaa90ac7b0adc0c8d21e5e7e1c66502d6b or later.
3. Inspect logs and annotations for any failure.
4. Confirm data/master/ remains unchanged and no template-derived archive files reappear.
5. Record governed evidence manifest, receipt, Merkle batch, log, summary, output commit, and passing run IDs.
```

## Known remaining files

```text
scripts/search_agent.py
  Refactor so canonical DataFrames are never mutated even transiently.

.github/workflows/ai_search_agent.yml
  Verify bounded successful run and governed evidence commit.

.github/workflows/auto_update.yml
  Verify successful governed local validation run.

.github/workflows/auto_update_tv_patch.yml
  Consider retirement after the primary workflow is verified to avoid duplicate validation surfaces.

FREE_DOM_MIRROR_HANDOFF.md
  Record final verification evidence.
```

## Archive readiness

This file contains the exact continuation state; earlier conversation context is not required.
