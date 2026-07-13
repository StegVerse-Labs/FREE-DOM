# FREE-DOM Mirror Handoff

## Source of truth

This is the current repository-local continuation record for `StegVerse-Labs/FREE-DOM`.

## Purpose and authority boundary

```text
Role: public evidence-first research and structured chronology
Canonical records: data/master/
Unverified leads: data/unverified/
Governed evidence: data/evidence/
Run logs: data/logs/ai_agent/
Derived summaries: data/summary/

Discovery is not verification.
Automation may not promote or persist changes into data/master/.
Templates are scaffolding and may not be ingested, promoted, or archived as records.
Cross-repository mutation, release, deployment, tagging, and record promotion are not authorized here.
```

## Current state

```text
MIRROR_HANDOFF_PRESENT
PORTABLE_OSINT_EVIDENCE_NODE_ACTIVE
AI_SEARCH_RUNTIME_BOUND_INSTALLED
AI_SEARCH_CANONICAL_READ_ONLY_IMPLEMENTED
AI_SEARCH_CANONICAL_READ_ONLY_TEST_INSTALLED
AI_SEARCH_CANONICAL_IMMUTABILITY_GATE_INSTALLED
PRIMARY_AUTO_UPDATE_MASTER_PROMOTION_REMOVED
PENDING_IMPORT_DEFAULT_DENY_INSTALLED
PENDING_TEMPLATE_EXCLUSION_INSTALLED
PENDING_IMPORT_GOVERNANCE_TEST_INSTALLED
ACTIVATION_READINESS_RECEIPT_INSTALLED
READINESS_SEMANTIC_CHECK_REPAIR_INSTALLED
FAILURE_RECEIPT_PERSISTENCE_INSTALLED
WORKFLOW_ARTIFACT_UPLOAD_ALWAYS_INSTALLED
LOCAL_VALIDATION_ARTIFACT_ONLY_INSTALLED
AI_SEARCH_SINGLE_WRITER_INSTALLED
AI_SEARCH_PRECOMMIT_REBASE_INSTALLED
STALE_RUN_CANCELLATION_INSTALLED
DUPLICATE_VALIDATION_WORKFLOW_RETIRED
AI_SUCCESS_RUN_RECEIPT_INSTALLED
AI_SEARCH_VERIFICATION_PASS
LOCAL_VALIDATION_POST_REPAIR_FAILURES_NONE_OBSERVED
SOURCE_HEALTH_PHASE_ACTIVE
SOURCE_URL_DEDUPLICATION_INSTALLED
SOURCE_FAILURE_CLASSIFICATION_INSTALLED
SOURCE_FAILURE_DEDUPLICATION_INSTALLED
SOURCE_HEALTH_RECEIPT_INSTALLED
SOURCE_HEALTH_TESTS_ENFORCED
SOURCE_HEALTH_RUNTIME_VERIFICATION_PENDING
```

## Activation evidence

```text
Successful AI workflow run: 29227794883
Run attempt: 1
Trigger event: push
Trigger SHA: 742ef288eb8c8cb10097a588b06aad6fc57ec47b
Workflow: AI Search Agent (Public OSINT Sweep)
Workflow output commit: fe7c6cbdefd2514b2d90994f5816f9f3d153b7c3
Run receipt: data/evidence/runs/ai-search-29227794883.json
Run result: PASS
Activation readiness result: PASS
Canonical write authority: false
Promotion authority: false
Artifact: free-dom-ai-search-verification-29227794883
Artifact ID: 8270475979
Artifact digest: sha256:e8a3dac0455f5d054bbeb3129dab1a2a9ea6ce07fa9d2ff2be0b2ffe56098eb3
Artifact size: 54453 bytes
Artifact retention expiry: 2026-08-12T06:07:33Z
```

### Canonical SHA-256 values recorded by the successful run

```text
data/master/master_batch_index.csv
39709efe398311b735c8f6ffb740cf9ee9466940caccdd0593f5072b496fceee

data/master/master_timeline.csv
33c46034ec3806f116ef27715d366abd7ab2bdd9128b7478308e51229df6e026

data/master/organizations.csv
a0ad86b60f249b51a512eb5dd475b925b4d9d301b8b4e9e0438503eadafefc30

data/master/photo_video_anchors.csv
df4ef39dfa00522e29d830a7b6a24c1eba8e605aa670e401d8f28061c762a7a3

data/master/verified_people_events.csv
a66ce41be9083b637fcfdbc3498aec6946d3b7ad8b06eb204227a5e270c1f027
```

All 21 activation governance checks in the successful run receipt passed. The successful commit changed only governed evidence, logs, summaries, and the repository-visible run receipt; no canonical file was part of the commit.

## Workflow topology

```text
Governed Local Validation
- contents: read
- artifact-only
- canonical immutability checks
- source-health deterministic tests
- no repository write authority

AI Search Agent
- bounded to 25 event targets and 25 person targets
- finite source timeout
- sole governed evidence writer
- canonical paths excluded from commit surface
- pre-commit rebase with autostash
- stale-run cancellation enabled
- successful runs publish machine-readable receipts
- source-health receipts are generated after each bounded sweep
```

## Source health and signal quality phase

```text
Source-health utility: scripts/source_health.py
Deterministic tests: scripts/test_source_health.py
Post-run builder: scripts/build_source_health_receipt.py
Receipt path: data/evidence/source-health/source-health-<run_id>.json
Schema: stegverse.free-dom.source-health.v1
Minimum healthy-source coverage: 0.50
Canonical write authority: false
Promotion authority: false
Source-manifest mutation authority: false
```

Installed behavior:

1. Configured source URLs are deduplicated before health measurement.
2. Repeated source failures collapse into one entry with `occurrence_count`.
3. Failures are classified as permanent, access-restricted, malformed, transient, unexpected-response, or unknown.
4. Healthy-source coverage is computed against unique configured sources.
5. Zero-hit runs remain valid bounded outcomes.
6. Source-health WARN does not grant authority to mutate canonical records or silently replace source manifests.
7. The duplicate PBS whitelist row was removed.

### Source-health commits

```text
Source-health classification and receipt utility: 53abef96501d1dd52e9d93ce44b7e343026b1cdf
Deterministic source-health tests: f06f4b84b0c642cf3c6c2b0332f20e1792886652
Post-run source-health builder: f03747b9a70dc8939ae866e61012668aa934f6b3
Duplicate PBS source removal: 1d344c7355c415d5c3de42226fb5ad822c34c722
AI workflow source-health enforcement: a207606396c8d992be8727e60d951c0e1d2ad367
Local validation source-health enforcement: 662eedf5e101bb2154564778b297367c0134ea0a
```

## Key activation repair commits retained

```text
AI runtime bound: 1e25e3335bf9e12edba5b020a41169aa5867f69d
Canonical read-only implementation: a5ddeb54d5df75e2cbf4ea030000d001e41c427c
Canonical read-only regression test: fa7b5dd4890cff8e8013efd1db5a1b1cf79528c9
Pending importer default-deny: d20bb2cf79338301930f145ae136677077184739
Pending governance test: 5e884d9ea911ca160c8330429152563559093c6c
Local validation artifact-only: 0e4325d2c9c52140c43a67c7ee202acb0b6c96fa
AI search sole writer: 571a679074ccb5fd7d40eee334f44c978f6935da
Pre-commit rebase hardening: db660b2b6bc0ee8b9094ad38c7266aca31cb5aa0
AI stale-run cancellation: 9e1440ab308e037e0b22f687be8a662fc802385c
Local validation stale-run cancellation: 6b274fea2aeb20b6ebb90f6a49a69eb781698eaa
Successful-run receipt: 742ef288eb8c8cb10097a588b06aad6fc57ec47b
Duplicate workflow retirement: 1e92c9016848a0fab80cd920cf5da37fe9ba2fdb
```

## Current verification target

```text
1. Observe AI Search Agent on a207606396c8d992be8727e60d951c0e1d2ad367 or later.
2. Confirm scripts/test_source_health.py passes.
3. Confirm data/evidence/source-health/source-health-<run_id>.json is committed.
4. Record healthy-source coverage and classification counts.
5. Confirm canonical SHA-256 values remain unchanged.
6. Use the health receipt to prepare governed source-manifest replacements for permanent or access-restricted endpoints.
```

## Next goal after runtime verification

```text
GOVERNED_SOURCE_MANIFEST_REPAIR
```

## Archive readiness

Activation remains complete and reconstructable. This handoff now also contains the exact continuation state for source-health runtime verification.