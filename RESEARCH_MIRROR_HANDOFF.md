# FREE-DOM Research Mirror Handoff

## Authority
- goal_id: ERL-RESEARCH-SURFACE-FREEDOM-001
- repository: StegVerse-Labs/FREE-DOM
- branch: main
- canonical_owner: StegVerse-Labs/Executive_Rhetoric_Ledger Issue #60
- local_role: Epstein-era public-source/event/court discovery and candidate production
- evaluation_authority: StegVerse-Labs/Executive_Rhetoric_Ledger for ERL-governed propositions
- local_privacy_authority: existing FREE-DOM ethics/privacy policy remains controlling for native records
- credential_authority: TV/TVC where applicable
- github_token_authority: NONE

## Claim
- state: CLAIMED_FOR_VALIDATION
- release_condition: deterministic populated trajectory fixture + ERL intake validation + registry promotion
- collision_boundary: native FREE-DOM verified/master/unverified semantics and privacy rules remain unchanged

## Installed authoritative files
- existing native `scripts/search_agent.py` and source-health/evidence machinery
- `research/README.md`
- `research/frontier.json`
- `research/acquisition_requests.jsonl`
- `research/source_candidates.jsonl`
- `research/research_receipts.jsonl`
- `research/conformance.json`
- `scripts/erl_research_agent.py`
- upstream standard: `StegVerse-Labs/Executive_Rhetoric_Ledger/standards/multi-trajectory-research-surface.v1.md`
- upstream transport: `StegVerse-Labs/Executive_Rhetoric_Ledger/contracts/research-candidate-transport.v1.md`

## Research posture
- recurrence: REQUIRED while active court/documentary/public-record trajectories remain unresolved;
- default cadence: weekly, adjusted by trajectory volatility;
- native FREE-DOM research is mixed research/ingest; ERL sidecar remains lead-only and cannot mutate native verified/master state;
- contradictory/null/new trajectories are preserved.

## Evidence
- ERL research layer: `440b646f8b3692be6c4d6f65199443c6aaa83632`
- conformance/recurrence profile: `93bb689c56f924182a6f241affae6303599e090f`
- adapter transport alignment: `4b48a1eb629cac726926e1e9237abad5d558cc59`
- native research evidence remains under `data/evidence/runs/` and separate from ERL trajectory candidate state.

The ERL-specific adapter now emits `stegverse.erl.research_source_candidate.v1`, records `native_records_mutated=false`, `evaluation_changed=false`, `privacy_policy_preserved=true`, TV/TVC credential authority, GitHub token authority NONE, and authority effect NONE.

## Remaining
1. run deterministic populated trajectory fixture against the ERL-specific adapter;
2. validate privacy/provenance/deduplication and no-auto-promotion behavior;
3. run emitted packet through ERL candidate intake validator;
4. promote registry entry to CONFORMING.

## Validation
- native FREE-DOM tests remain authoritative for native research
- `python scripts/erl_research_agent.py --base . --dry-run`
- `python <ERL>/scripts/validate_research_surface.py .`
- `python <ERL>/scripts/validate_research_candidate_intake.py research/source_candidates.jsonl`

## Completion accounting
- ERL-specific developed-files: 7/7 = 100%
- scaffolding/stubs: 0
- validation: 0/3
- integration: 2/3
- goal-activation: 75%
