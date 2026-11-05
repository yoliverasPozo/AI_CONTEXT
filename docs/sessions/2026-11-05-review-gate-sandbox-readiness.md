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
The implementation passes 43 focused tests and all 161 tests. Independent
security review reproduced the historical PR #16 result using real evidence
in a simulated open scope, with 11 sensitive documentation files and 16 reads.
PR #14's historical clean review remained eligible. The simulated status tests
cover shared SHA visibility, late findings, lifecycle changes, missed and
duplicate events, write failure and races.
An explicit acceptance paragraph keeps a quoted disposition marker from
counting as an owner's decision.

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


## November 5 follow-up on PR #17

The owner made PR Lens advisory. The current policy requires authenticated,
completed Codex review on the exact head, required CI and resolved conversations.
PR Lens rendered the previous head without an authenticated terminal review or
skip. A missing verdict stays advisory. Verified unresolved findings block.

The evaluator now preserves known bot-authored findings from retained comment
and review history and supports an exact-diff disposition by the pinned owner.
The simulator reserves invocation generations before its first read. Timestamps
compare timezone-aware instants. A missing required Codex comment after a
successful collection reaches terminal simulated failure on a stable scope.

Independent review found gaps in malformed timezone handling and retained
finding coverage for minimized or edited evidence and resolved inline threads.
The corrections preserve findings published at or after an authenticated
re-review begins. The independent recheck found no actionable blockers.
All 54 focused and 172 total tests passed.

Keep PR #17 Ready for Review. Confirm fresh Codex and CI on the published
revision, and obtain separate owner authorization for any merge. A live
sandbox needs a durable evidence ledger and separate authorization.

Codex found that a verified re-review could not supersede an older standalone
issue comment alongside the sticky. The evaluator now determines the unique
authenticated re-review cutoff before assessing any issue-comment findings.
The added regression reproduced the failure in both comment orders, and
checks findings from before, at, during and after the review start.
