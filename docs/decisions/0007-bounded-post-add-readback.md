# Decision: Bounded post-add readback stabilization

## Status

Experimental. No live pilot or recurring activation is authorized by this change.

## Context

A supervised acknowledged add's readback reported different totals on successive
pages; independent complete state was correct. Rejecting mixed pages was safe.
A fresh, bounded read can seek a complete snapshot without resending the add.

## Decision

Optional verification policy permits1..5 attempts,1..120 seconds and1..30 calls.
Defaults:1 attempt,30 seconds,10 calls; more than1 requires rate_floor>=200.
Existing lifetime call cap, per-attempt page cap and per-response rate floor remain
in force. Only the internal
count-change guard can restart, only within this newly acknowledged add.

Each attempt starts at cursor=None with fresh page/item sets. Validate item shape,
explicit archive state, field identities/uniqueness, original values, scope/head
and cursor validity before a restart. Genuine drift, malformed evidence, unknown
errors and exhausted budgets stop. Durably record each failure before another
read. A complete fresh snapshot still passes all final preservation invariants.

At a terminal page, verify the observed IDs contain every approved original,
including archived originals, before a count mismatch can trigger another read.
Otherwise a later stable snapshot could hide an omission observed in a completed
attempt. Count overflow and incomplete-page checks also precede restart eligibility.

A monotonic deadline bounds read transport timeouts, attempts, evidence persistence
and final state validation. Check it immediately before acceptance. Final receipt
fsync cannot itself be interrupted or guaranteed to finish within that deadline.
Any failed check leaves the mutation intent spent.

## Alternatives Considered

- Single immediate read: remains the default.
- Merge pages or take maximum count: rejected; invents a snapshot.
- Broad error retry or mutation resend: rejected; may hide drift/duplicate work.
- Promote historical needs_review later: rejected; recover only observes.

## Rationale

A new complete snapshot must independently satisfy approval and preservation
requirements. Typed restart eligibility, shared budgets, partial-data validation
and durable evidence contain the ambiguity without adding mutation authority.

## Consequences

Opt-in spends more measured read points. Review exact verification budgets with
source/config before operator approval; changed budgets require renewed review.
No proposal-schema expansion. The first pilot's lost failure could be consistent
with count instability, but its cause remains unproven. Further supervised
acceptance and unattended operation remain separate gates.
