# Session: Diagnostic coverage and bounded verification stabilization

Date: 2026-11-04

## User Goal

Verify PR Lens's two correctness findings on merged PR12, audit all reader errors,
add focused regressions, investigate bounded configurable read-only stabilization
after an inconsistent count, preserve fail-closed behavior/original receipts,
prepare a draft PR with full suite and independent review. No live Project writes,
schedules, credentials or production systems are authorized.

## Investigation

Clean main base4e506b29ae458cb138b0b719d8cf9607e68deb5f,98 tests pass. Read the
actual PR Lens comment on PR12 at1795e17; both findings hold and overlap. Several
known relation/identity/unavailable-node guards were missing from the allowlist.
All literal writer_github guards and invoked normalization/collector helper
guards are now audited in docs/reviews/2026-11-04-reader-error-coverage.md.

A later pilot's retained evidence identifies a count change within one read.
No mutation needs resending. Fresh bounded pagination can seek a new complete
snapshot, while the earlier pilot's lost observation remains unproven. Private
original receipt inventories are recorded/verified outside the public repository;
neither operation is applied, recovered, rebuilt or changed in this work.

## Decisions

Only an internal typed count-change exception may restart a post-ack read. Default
one attempt; opt-in policy1..5 attempts/1..120 seconds/1..30 calls and floor>=200
for retries. Shared lifetime budgets, monotonic deadline/transport timeout and final
acceptance check. Fresh cursors/sets per attempt, full partial-item/field/archive/
cursor validation before retry eligibility, complete original-state validation
before acceptance. Every attempt recorded; persistence failure stops. Historical
spent operations never promote. See ADR0007 and implementation plan.

## Changes Made

- Completed fixed diagnostic mappings, with trusted validation types only; unknown
  runtime errors cannot become retryable by matching a message string.
- Added optional verification policy, bounded fresh-read loop, per-attempt durable
  evidence and sanitized final summary. Mutation transport remains single-attempt.
- Shared item validator between complete snapshots and observed partial items.
- Added optional collector transport timeout (default45 unchanged), allowing only
  the writer verification path to bound each query by its remaining deadline.
- Updated generic disabled example, operator guide/ADR/current context, audit and
  focused tests. CLI/core/workflow entry points remain unchanged.

## Tests

117 tests pass, checkout-local src provenance. RED/GREEN evidence covers missing
PR Lens codes, transient/persistent counts, eventual stable snapshots, unrelated
additions/deletions, original/field/archive drift, unknown exceptions, floor/call/
time exhaustion, repeated cursors, malformed partial fields, evidence fsync failure,
deadline through final normalization and fresh config against a spent operation.
No test calls GitHub. Independent reviewer also tested a real local sleeping
subprocess: one-second bound passed a remaining timeout and stopped safely.

## Problems Encountered

Review found partial target archive/field validation could be hidden by the count
guard, repeated cursor checking came too late, and the deadline ended before
final policy validation. Each reproduced with a failing test and fixed. Additional
regression prevents arbitrary RuntimeError message matching from enabling retry.
Final independent review found no remaining actionable implementation finding.
Final receipt fsync is not interruptible; deadline bounds acceptance decision,
including preceding validation/evidence work, not a hardware completion guarantee.

## Current Result

Reviewable opt-in read stabilization with default single read, zero mutation retries
and unchanged approval/preservation gates. Unknown errors and genuine drift stop.
Original pilot causes/results remain unchanged. Exact-head CI/delivery evidence
belongs in the draft PR; private receipt preservation proof stays local.

## Next Steps

Review source and budgets; prefer a new absent-target supervised pilot after the
reviewed revision is accepted. Obtain fresh900-second exact-source/config/digest/
expiry/one-attempt authority, observe all attempt evidence and independent final
state. No old target removal/re-add, historical promotion or unattended activation.
