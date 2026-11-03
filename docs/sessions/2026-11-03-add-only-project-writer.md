# Session: Disabled add-only Project writer

Date: 2026-11-03

## User Goal

Implement the next central synchronization stage as a disabled, add-only writer;
preserve existing Project items/fields; add exact-state gates, duplicate prevention,
failure recovery, before/after receipts and rollback tests. Prepare a draft PR
with independent review. No live writes, more credentials, schedules or routing
changes. A private one-item pilot plan remains a separate authorization stage.

## Investigation

Read current main, context, prior Project ADR/session and the private November 3
live-read acceptance. PR #10 is merged; base is
`d0c9cbf770d12d505b08210c3ed42f9ae0cded4b`. Baseline 49 tests passed with the
correct `src` import. GitHub documents that add may return an existing item ID;
there is no created-by-this-call flag or atomic CAS. A read-only schema check of
the new reader succeeded against current complete membership/fields. Its nested
all-field reads cost substantially more than the earlier selected-field planner.
Private snapshots and exact pilot identifiers are kept outside this public repo.

## Decisions

Separate source-only CLI and fixed mutation; user-owned Projects/same-owner open
PRs only. Explicit enabled config, execution flag, exact proposal digest and
short expiry. Recheck complete archived/unarchived membership, definitions and
all populated supported values. Persist intent before sending at most one add;
recovery never resends. Unknown fields/read errors fail closed. A no-op also
spends the operation. Rollback is a non-executable manual proposal requiring
separate authorization. See ADR 0006 and the design/implementation plan.

## Changes Made

- Added `writer.py`, `writer_journal.py`, `writer_github.py`, `writer_cli.py` and
  disabled generic config, separate from installed initializer and planner.
- Added controlled-transport policy, reader, mutation, CLI, failure and rollback
  tests; no test invokes a real GitHub mutation.
- Added operator guide, experimental ADR, design/plan, and current context updates.

## Tests

Baseline 49 tests; final local and independent runs passed **85 tests** using
checkout-local imports. [Independent review](../reviews/2026-11-03-add-only-writer.md)
found no remaining blockers after fixes. Exact-head natural CI is recorded in
the draft PR. Tests first failed for missing implementations,
then exercised expected scope/head/field drift, archived duplicates, terminal
no-op replay, intent/acknowledgment failures, timeouts, post-read drift, lock and
journal corruption, approval expiry around preflight/fsync, recovery size bounds,
redacted relations, pagination, transport uncertainty and guarded rollback.

## Problems Encountered

Independent review reproduced redacted populated repository/milestone values
passing completeness and recovery appends exceeding the journal limit. Added
regressions; relation identities now fail closed and capacity is checked before
writing. Approval expiry is rechecked after preflight and intent fsync. A no-op
replay previously could add after another actor removed the item; it is now terminal.
The first canonical-after test incorrectly assumed item order, corrected to
compare identity maps. Schema introspection's two-field limit required splitting
queries; no credentials were inspected or changed.

## Current Result

Disabled implementation independently reviewed, with no live mutation or
recurring activation. Current private live-reader receipt is unapproved. Original
planner, initializer, workflow files and routing contracts are unchanged.

## Next Steps

Finish exact-head review/CI and obtain separate single-item pilot authorization
against a fresh private proposal; do not reuse the schema-check operation. Keep
uncertain outcomes and all changed human fields intact. No automatic rollback,
scope expansion or recurring activation is implied by this PR.
