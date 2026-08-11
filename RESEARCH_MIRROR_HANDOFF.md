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
- release_condition: deterministic trajectory fixture validation plus ERL registry promotion
- collision_boundary: native FREE-DOM verified/master/unverified semantics and privacy rules remain unchanged

## Installed authoritative files
- existing native `scripts/search_agent.py` and source-health/evidence machinery
- `research/README.md`
- `research/frontier.json`
- `research/acquisition_requests.jsonl`
- `research/source_candidates.jsonl`
- `research/research_receipts.jsonl`
- `scripts/erl_research_agent.py`
- upstream standard: `StegVerse-Labs/Executive_Rhetoric_Ledger/standards/multi-trajectory-research-surface.v1.md`

## Evidence
- handoff: `a897914b1a85e922add0a48e29ed552214262937`
- ERL research layer: `440b646f8b3692be6c4d6f65199443c6aaa83632`
- native research evidence already exists under `data/evidence/runs/` and remains separate from ERL trajectory candidate state.

The ERL-specific adapter writes only under `research/`, explicitly records `native_records_mutated=false`, preserves lead-only posture, and does not replace the existing FREE-DOM agent.

## Remaining
1. run deterministic populated trajectory fixture against the ERL-specific adapter;
2. validate privacy/provenance/deduplication and no-auto-promotion behavior;
3. ERL candidate intake/transport validation;
4. promote registry entry to CONFORMING.

## Validation
- native FREE-DOM tests remain authoritative for native research
- `python scripts/erl_research_agent.py --base . --dry-run`
- `python <ERL>/scripts/validate_research_surface.py .`

## Completion accounting
- ERL-specific developed-files: 6/6 = 100%
- scaffolding/stubs: 0
- validation: 0/3
- integration: 1/2
- goal-activation: 65%
