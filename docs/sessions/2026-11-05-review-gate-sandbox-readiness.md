# Session: Review gate compatibility and sandbox readiness

Date: 2026-11-05

## User Goal

Handle authenticated PR Lens documentation skips and prepare a non-enforcing
publisher simulation. Publish a Ready for Review PR. Live statuses, credentials,
rules, Project operations and merges are outside this scope.

## Investigation

Both prerequisite PRs were merged at main
`568ad14c8a2724c1f8c81cf28130e7868ecfa663`. PR #16's authentic skip notice
had no SHA and its exact head had no PR Lens check. Its file list contained
agent and coordination instructions. The clean Codex marker and four successful
CI jobs applied to the exact PR head.

## Decisions

Use immutable tree differences to verify the PR file list. Recognize the
observed skip and require an exact-scope owner disposition for its unversioned
notice. Executable or mixed diffs require full review. Keep the in-memory
publisher disabled by default and native status advisory.

## Changes Made

Added the change classifier, authenticated skip disposition, lifecycle checks
and pending/success/failure simulator. Documented the approval, rollback, event
and cost boundaries in the [operating guide](../AI_REVIEW_GATE.md) and
[ADR 0009](../decisions/0009-documentation-skip-and-sandbox-status.md).

## Tests

Baseline 137 tests passed. New skip tests failed against the old evaluator.
The implementation passes 42 focused tests and all 160 tests. Independent
security review reproduced the historical PR #16 result using real evidence
in a simulated open scope, with 11 sensitive documentation files and 16 reads.
PR #14's historical clean review remained eligible. The simulated status tests
cover shared SHA visibility, late findings, lifecycle changes, missed and
duplicate events, write failure and races.

## Problems Encountered

GitHub's filtered timeline total included unfiltered events. The observer now
requires a terminal filtered page and handles the total separately. Independent
review also caught cross-scope receipt reuse and disposition renewal after a
base advance. Regression tests cover both corrections. Real status publication
still has commit-wide visibility and a same-head invalidation race.

## Current Result

Status: review

Current owner: Codex implementer

Next owner: repository owner

Work branch: `feat/review-gate-sandbox-readiness`

The PR records its published SHA, CI and automated reviews.

## Next Steps

Review the implementation and authorize any merge separately. If a sandbox
pilot is desired, identify the disposable repository, PR, head and target
branch, review the pinned adapter and App permissions, and authorize a bounded
advisory publication. Retain manual verification at the merge decision.
