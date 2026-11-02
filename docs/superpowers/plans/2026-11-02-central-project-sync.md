# Central project sync prototype implementation plan

> Execution: native implementation in the already isolated checkout, followed by independent parent review. The user explicitly authorized execution and a draft PR; no further plan approval is required.

**Goal:** Produce bounded, reviewable GitHub Project reconciliation proposals without any write capability.

**Architecture:** An optional standard-library example reads an explicit configuration and either an offline snapshot or GitHub GraphQL through an existing `gh` login. A pure planner proposes additions and strictly verified blank actor fills while preserving manual state and approval holds. It emits notification/cursor proposals without delivering messages or saving cursors.

**Tech Stack:** Python 3.10+, unittest, existing GitHub CLI for optional reads.

**Spec:** [PROJECT_SYNC.md](../../PROJECT_SYNC.md), implemented with this plan.

## Global constraints

- Core initializer, packaged resources and default runtime remain offline and unchanged.
- No executable write/apply path, credentials, scheduler or new workflow.
- Public examples use generic data; private inventory and authentication diagnostics stay outside Git.
- Read all project identities including archived items; paginate bounded collections and fail closed on incomplete reads, errors, duplicate identities, depleted rate limits or exhausted budgets.
- Labels/Project fields are advisory; no assignee inference, removal, dependency/gate/status writes or implicit authorization.

## Review focus

1. Archived identities and repeated cursors must prevent duplicates and incomplete plans.
2. Actor proposals require matching exact-head journal, marker and label; conflicts and stale observations remain unknown.
3. Manual actor fields, approval gates and blocked statuses must survive terminal PR reporting.
4. Existing tracked closed/merged PRs must be read even when absent from open-repository results.
5. Authentication failures and external text must not leak credentials or become executable input.

## Task 1: Planner and offline CLI

Files: `examples/project_sync/{__init__,planner,__main__}.py`, generic configuration/snapshot, `tests/test_project_sync.py`.

- [x] Write failing tests for allowlist validation, identity/idempotence, archived/manual preservation, terminal suggestions, verified/conflicting/stale handoffs and cursor deduplication.
- [x] Run the tests, confirm feature absence fails, implement `validate_config(config)`, `plan(config, snapshot, cursor=None)` and literal coordination parsing.
- [x] Exercise the CLI with a generic snapshot and assert a read-only proposal; reject unsupported apply arguments and invalid inputs.

## Task 2: Bounded live collector

Files: `examples/project_sync/collector.py`, collector tests in `tests/test_project_sync.py`.

- [x] Write failing tests using complete GraphQL response fixtures for pagination, tracked terminal PRs, relevant issues, handoff readback, budget/rate/errors/truncation and duplicate cursors.
- [x] Implement `collect(config, client)` plus `GhClient`; only hardcoded GraphQL queries and existing login are used.
- [x] Run tests and the authorized live read once; record scope failure generically without granting scopes.

## Task 3: Documentation, verification and review

Files: `docs/PROJECT_SYNC.md`, ADR 0005, current context, inbox refinements, dated session, README pointer.

- [x] Document schemas, quickstarts, explicit auth boundary, snapshot attribution, conservative central periodic design, apply deferral and recovery requirements.
- [x] Correct public repository state without claiming acknowledged handoff or broader activation.
- [x] Run the full existing suite with import provenance, generic CLI simulation, whitespace and public-data review.
- [ ] Resolve the requested independent parent review and publish the draft PR without merge or activation. Candidate sent; publication pending.
