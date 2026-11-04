# Decision: Disabled single-item add-only Project writer

## Status

Experimental. Implementation/review does not authorize a live pilot or schedule.

## Context

The November 3 private live-read validation established complete current
repository and archived/unarchived Project reads. The plan-only adapter can
identify missing PRs, but applying its whole result would mix membership, fields
and handoff authority. The next requested stage is a narrowly reviewable writer.

## Decision

Ship a separate source-only CLI, disabled config, one exact-head same-owner PR,
one approved state digest, bounded complete-state rechecks, fsynced hash-chained
before/intent/acknowledgment/after receipts and at most one add attempt. Recovery
only reads; rollback only proposes a separately authorized manual decision.
No fields, existing items, schedules, credentials or agent routing are modified.

## Alternatives Considered

- Execute all planner proposals: excessive scope and ambiguous authority.
- Automatic compensating deletion: cannot prove item creation ownership.
- Bulk or scheduled writer: deferred until a separately approved pilot provides
  measured evidence and operational recovery experience.

## Rationale

GitHub's [add operation](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)
can return a preexisting item ID. No atomic CAS spans the recheck/add, so a lost
response or concurrent addition cannot justify deletion. A durable spent intent
and read-only reconciliation preserve uncertainty without duplicate retries.

## Consequences

Tests can establish local safety behavior without real mutation or more scopes.
Complete reads cost more than the planner's selected-field reads. Unsupported
populated fields stop execution. User-owned Projects only; single operator and
private local receipts are required. Native automations may populate new-item
defaults. Concurrency and filesystem durability remain bounded, not transactional
guarantees. Existing routing conflicts remain owner-managed under ADRs 0003/0004.

2026-11-04 diagnostic supplement: new needs_review receipts retain fixed sanitized
failure codes, stage, bounded page/rate fingerprints and complete normalized
observations when available. Historical receipts remain immutable and readable;
no lost snapshot is reconstructed. Diagnostics add no retries, acceptance bypass
or mutation authority. See [diagnostic contract](../PROJECT_WRITER_DIAGNOSTICS.md).
