# Session: AI review completion gate

Date: 2026-11-05

## User Goal

Prepare a reviewable evaluator for Codex and PR Lens completion, findings and
existing CI on the current PR head. Investigate GitHub Pro enforcement,
event costs, spoofing and rollback. Scope includes simulation and a draft PR.
Merging, native enforcement, credential changes and Project operations require
separate authority.

## Investigation

Main was `810a7388e1989558e1e787a81cd66d19c6fa21c8`, unprotected with no
rulesets. Verified the reviewer App and bot IDs against GitHub metadata and
observed authenticated edit history for PRs 13 and 14. PR Lens's drawing check
and review completed separately. The original handoff workflow reconciles
advisory labels and contributes no gate evidence.

## Decisions

Use the observed bot contracts in a read-only observer. Simulate the fixed
status request and evidence rechecks with a test publisher. Require exact-head
clean re-review and resolved conversations for automated disposition. Defer
publication wiring until shared-SHA isolation and revocation are validated.

## Changes Made

- Added the optional evaluator, bounded GitHub reader, and observe CLI.
- Added tests of review states, provenance, CI origin, pagination, duplicate
  events and fail-closed publication.
- Documented the proposed ruleset, cost, event delivery and staged rollback.

## Tests

The test-first run failed before the evaluator existed. All 19 focused tests
and all 137 tests in the full suite passed. The focused suite
exercises both reviewer pending states, findings, fresh re-review, head races,
comment tampering, incomplete data, handoff labels, deduplication and publisher
failure. An isolated historical replay on merged PRs used a simulated open
scope. PR #13 blocked on an unresolved thread and PR #14 passed its retained
clean review evidence. The live read-only CLI blocked PR #7 on an unsupported
PR Lens marker and PR #8 on an unresolved conversation. Each live read used
nine API calls. The live PR #8 probe took about six seconds. The independent
reviewer also ran the focused suite and reproduced the PR #8 block.

## Problems Encountered

Initial independent review found that the PR Lens short SHA and drawing marker
could be combined with stale review prose. The evaluator now requires the
authenticated full-head pending-to-clean transition in retained history.
A separate same-head bot submission and a contradictory Codex security report
also block. The provider history format remains an observed contract.
GitHub commit statuses cannot natively bind a pass to one PR or atomically
revoke a pass when same-head evidence changes.

## Current Result

Task status: review

Current owner: Codex implementer

Next owner: repository owner

Branch: `feat/ai-review-completion-gate`

The observer and simulated publisher are available for review.
See the [operating guide](../AI_REVIEW_GATE.md) and
[ADR 0008](../decisions/0008-review-gate-observation.md).
The PR head and CI evidence are recorded in the draft PR.

## Next Steps

Review the draft and approve the next stage separately. Validate a dedicated
publisher, required-check SHA selection, shared-head isolation, provider event
delivery and fail-closed revocation in a sandbox before proposing a required
rule on main. Record a human merge decision independently.
