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
Source replacement or reactivation requires a governed manifest update and evidence trail.
```

## Current state

```text
MIRROR_HANDOFF_PRESENT
PORTABLE_OSINT_EVIDENCE_NODE_ACTIVE
AI_SEARCH_VERIFICATION_PASS
LOCAL_VALIDATION_ARTIFACT_ONLY
AI_SEARCH_SINGLE_WRITER
CANONICAL_WRITE_AUTHORITY_FALSE
PROMOTION_AUTHORITY_FALSE
SOURCE_HEALTH_PHASE_ACTIVE
SOURCE_URL_DEDUPLICATION_INSTALLED
SOURCE_FAILURE_CLASSIFICATION_INSTALLED
SOURCE_FAILURE_DEDUPLICATION_INSTALLED
SOURCE_HEALTH_RECEIPT_INSTALLED
SOURCE_HEALTH_TESTS_ENFORCED
GOVERNED_SOURCE_MANIFEST_INSTALLED
SOURCE_MANIFEST_VALIDATOR_INSTALLED
SOURCE_MANIFEST_REGRESSION_TESTS_INSTALLED
ACTIVE_SOURCE_PROJECTION_INSTALLED
STABLE_SOURCE_ID_PROJECTION_REPAIR_INSTALLED
SOURCE_HEALTH_RUNTIME_VERIFICATION_PENDING
```

## Activation evidence retained

```text
Successful AI workflow run: 29227794883
Trigger SHA: 742ef288eb8c8cb10097a588b06aad6fc57ec47b
Workflow output commit: fe7c6cbdefd2514b2d90994f5816f9f3d153b7c3
Run receipt: data/evidence/runs/ai-search-29227794883.json
Run result: PASS
Activation readiness result: PASS
Canonical write authority: false
Promotion authority: false
Artifact: free-dom-ai-search-verification-29227794883
Artifact ID: 8270475979
Artifact digest: sha256:e8a3dac0455f5d054bbeb3129dab1a2a9ea6ce07fa9d2ff2be0b2ffe56098eb3
```

### Canonical SHA-256 values

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

## Source health and signal quality

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
2. Repeated failures collapse into one entry with `occurrence_count`.
3. Failures are classified as permanent, access-restricted, malformed, transient, unexpected-response, or unknown.
4. Healthy-source coverage is measured against unique active sources.
5. Zero-hit runs remain valid bounded outcomes.
6. Source-health WARN does not grant authority to modify canonical records or silently replace sources.

## Governed source lifecycle

```text
Lifecycle manifest: data/sources/source_manifest.csv
Active execution projection: data/sources/sources_whitelist.csv
Validator: scripts/validate_source_manifest.py
Regression tests: scripts/test_source_manifest_governance.py
```

Lifecycle rules:

1. Every source has a stable `source_id`.
2. `source_id`, source type, and URL define execution identity; display names may change without changing standing.
3. Allowed states are `active`, `quarantined_pending_revalidation`, and `retired`.
4. The active whitelist must exactly match active manifest rows by stable identity.
5. Duplicate source IDs and duplicate manifest URLs fail validation.
6. Non-active sources must declare replacement or revalidation posture.
7. Every entry must retain `evidence_ref` and `authority_ref`.
8. No guessed replacement endpoint is authorized.
9. Quarantined sources remain visible in the manifest and are not silently deleted.

The activation run evidence moved the following sources into `quarantined_pending_revalidation`:

```text
CourtListener NYSD RSS - permanent/404
Reuters US - access-restricted/401
Reuters World - access-restricted/401
AP Top News landing page - malformed RSS configuration
C-SPAN Recent Programs - permanent or unexpected response
PBS NewsHour legacy RSS - permanent/404
C-SPAN site landing - unexpected response/202
Reuters UK - access-restricted/401
```

The active projection currently contains six sources that did not report retrieval failure in the activation run:

```text
SRC-HOUSE-OVERSIGHT-RSS
SRC-NYT-US
SRC-WAPO-POLITICS
SRC-HOUSE-OVERSIGHT-SITE
SRC-GUARDIAN-UK
SRC-ABC-TOP
```

Quarantine is not a factual claim that a publisher is unavailable. It records only the bounded retrieval result and prevents repeated unhealthy requests pending governed revalidation or replacement.

## Failed post-manifest verification and repair

```text
AI Search run: 29277069036
Trigger commit: 54a2a7a868f1b18324bbacedd748ed00c56065d2
Result: FAIL at Validate governed source manifest
Passed before failure: zero-hit evidence test, source-health tests
Failure artifact upload: PASS

Governed Local Validation run: 29277088115
Trigger commit: b5a8894fb49a0bd3c1cd69d315b8920501792cb0
Result: FAIL at Validate governed source manifest
Passed before failure: pending-import governance, zero-hit evidence test, source-health tests
Failure artifact upload: PASS

Root cause: the first validator compared mutable display names. The manifest and whitelist represented the same active URLs but used different legacy labels.

Stable-ID whitelist repair: 2124cba44bc80ac3890df1820fa90975a3176fdc
Stable-ID validator repair: cc390f2cbf5880ba9aa850449016be5dfe5bed57
Stable-ID regression repair: 192b72094c5dd9475bf218c9811df8ad4f4c443b
```

## Source-governance commits

```text
Source-health utility: 53abef96501d1dd52e9d93ce44b7e343026b1cdf
Source-health tests: f06f4b84b0c642cf3c6c2b0332f20e1792886652
Source-health builder: f03747b9a70dc8939ae866e61012668aa934f6b3
Duplicate PBS removal: 1d344c7355c415d5c3de42226fb5ad822c34c722
AI source-health enforcement: a207606396c8d992be8727e60d951c0e1d2ad367
Local source-health enforcement: 662eedf5e101bb2154564778b297367c0134ea0a
Governed source manifest: bdaf2f666c89cfd63955142b82306a37ceafd45c
Manifest validator: d13e8f6fa11cdf451a827a5d1c9d2b81f301bee0
Active whitelist projection: d1cf37a860bd953dc03fa30bd2127e789d087218
Manifest regression tests: 652561fff564b3a5381eccd2ce774c2cd7c08817
AI manifest enforcement: 54a2a7a868f1b18324bbacedd748ed00c56065d2
Local manifest enforcement: b5a8894fb49a0bd3c1cd69d315b8920501792cb0
```

## Current verification target

```text
1. Observe AI Search Agent on 192b72094c5dd9475bf218c9811df8ad4f4c443b or later.
2. Confirm scripts/test_source_health.py passes.
3. Confirm scripts/test_source_manifest_governance.py passes.
4. Confirm scripts/validate_source_manifest.py reports PASS by stable source_id.
5. Confirm a new data/evidence/source-health/source-health-<run_id>.json is committed.
6. Record healthy-source coverage and classification counts.
7. Confirm source_manifest_validation=PASS in the durable workflow receipt.
8. Confirm canonical SHA-256 values remain unchanged.
```

## Next goal after runtime verification

```text
GOVERNED_SOURCE_REVALIDATION_AND_REPLACEMENT
```

Replacement work must use publisher-confirmed endpoints or explicit evidence. No source is reactivated solely because a plausible URL can be guessed.

## Archive readiness

Activation remains complete and reconstructable. This handoff contains the exact continuation state for governed source-health runtime verification and source lifecycle repair.
