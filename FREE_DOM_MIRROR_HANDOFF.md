# FREE-DOM Mirror Handoff

## Source of truth

This file is the current repository-local handoff and task source of truth for `StegVerse-Labs/FREE-DOM`.

It was created after a cross-repository handoff scan found no existing `*_MIRROR_HANDOFF.md` in this repository.

## Repository purpose

```text
Repository: StegVerse-Labs/FREE-DOM
Role: public evidence-first research and structured factual chronology
Primary users: researchers, investigative journalists, educators, and fiction authors
Evidence posture: publicly verifiable sources, reproducible records, and version traceability
Sensitive-data posture: identifying testimony, private allegations, and protected personal information must not enter the public repository
```

The repository separates:

```text
data/master/      verified canonical datasets
data/pending/     submissions awaiting review
data/unverified/  leads and unconfirmed material
data/sources/     monitored public-source definitions
data/logs/        agent and processing logs
data/summary/     derived status and indexes
data/archive/     processed snapshots retained for audit
```

## Current workflow surface

The following workflow files are present and must be evaluated independently:

```text
.github/workflows/ai_search_agent.yml
.github/workflows/auto_update.yml
.github/workflows/forward-to-bridge.yml
.github/workflows/auto_update_tv_patch.yml
.github/workflows/bootstrap_tv_policy_repo.yml
.github/workflows/test-readiness.yml
```

Workflow presence is not proof that a workflow is current, safe, green, authorized for cross-repository action, or suitable for production use.

## Current state

```text
MIRROR_HANDOFF_PRESENT
REPOSITORY_PURPOSE_DECLARED
PUBLIC_EVIDENCE_ONLY_BOUNDARY_DECLARED
SENSITIVE_INFORMATION_PUBLICATION_PROHIBITED
WORKFLOW_INVENTORY_RECORDED
CURRENT_MAIN_WORKFLOW_VERIFICATION_PENDING
CROSS_REPOSITORY_FORWARDING_AUTHORITY_NOT_INFERRED
AUTOMATED_MASTER_PROMOTION_AUTHORITY_NOT_INFERRED
RELEASE_AND_DEPLOYMENT_AUTHORITY_NOT_GRANTED
```

## Authority boundary

```text
Discovery is not verification.
A source mention is not proof of the underlying claim.
An unverified lead is not admissible as a verified master record.
Automation output is not final editorial or legal authority.
Workflow success is not evidence admissibility.
Repository access is not cross-repository mutation authority.
Bridge forwarding is not destination acceptance.
Pending data must not be promoted to master solely because automation can process it.
No private testimony, identifying allegation, credential, protected personal data, or non-public evidence may be published through this repository.
No release, deployment, tag, merge, external notification, referral, or public accusation is authorized by this handoff.
```

## Permitted bounded maintenance

The following repository-local actions are permitted when directly required by a verified failure and when they preserve the boundaries above:

```text
repair syntax errors
repair stale file-path or exact-token assertions
repair repository-local schema validation
repair canonical versus iOS-safe workflow parity
repair documentation links and workflow inventory
add deterministic tests for existing behavior
record workflow evidence and blockers
update this handoff
```

The following actions require separate explicit authority:

```text
promote records from unverified or pending into master
change evidentiary classification
publish identifying or sensitive information
forward data to another repository or external system
modify another repository
enable credentials or secrets
send referrals or communications
merge pull requests
release, deploy, or tag
change source allowlists or collection scope in a way that broadens surveillance or personal-data collection
```

## Completion conditions for the current phase

The repository-local verification phase is complete only when all of the following are evidenced on the same current-main commit or a documented successor:

```text
all workflow YAML parses successfully
all repository-local tests and readiness checks pass
workflow references resolve to existing files
master, pending, unverified, and archive boundaries remain explicit
no automated path promotes unverified material to master without a declared review gate
no workflow silently requires unavailable secrets
cross-repository jobs fail closed when destination authority or credentials are unavailable
public outputs preserve source attribution, uncertainty, privacy, and non-implication boundaries
passing run identifiers and commit SHA are recorded in this handoff
```

## Next task

```text
1. Correlate the newest unread GitHub failure or progress notification to its exact FREE-DOM workflow run and current-main commit.
2. Inspect the failing job, step, logs, and artifact evidence.
3. Determine whether the failure is repository-local and covered by Permitted bounded maintenance.
4. Apply only the smallest non-destructive repair when authorized.
5. Verify the repaired workflow or test on the repair commit or later.
6. Record the run ID, job, commit SHA, repair commit, result, and next task in this handoff.
7. Stop before any record promotion, external forwarding, credential use, publication expansion, release, deployment, tag, or cross-repository mutation unless separately authorized.
```

## Evidence to preserve

```text
notification subject and timestamp
repository and branch or pull request
workflow run ID
job and first failing step
commit SHA
failure classification
relevant logs or artifact digest
repair commit SHA, when applicable
verification run and conclusion
remaining blocker or next declared task
```

## Archive readiness

This handoff records the repository purpose, workflow inventory, evidence and privacy boundaries, permitted maintenance scope, completion conditions, and exact continuation order. Earlier conversation context is not required to begin bounded repository-local diagnosis.