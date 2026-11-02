# Decision: Trial a central plan-only GitHub Project projection

## Status

Experimental (2026-11-02)

## Context

The optional inbox makes handoffs discoverable, but labels, journals, manual
Project fields and lifecycle events can disagree. Extending the same workflow
to every repository adds maintenance and repeated work. A controller must not
turn a routing hint, merged PR or populated Project field into authority.

## Decision

Prototype one explicitly configured central reconciliation adapter under
`examples/project_sync/`, outside the core initializer. Use Python's standard
library and an existing `gh` login for bounded GraphQL reads; support offline
simulations with the same planner. Output proposals only. No apply, credentials,
scheduled workflow, agent invocation or notification delivery is installed.

Use content node identities including archives to avoid duplicates. Propose
only missing open PR/explicit issue additions and blank actor fills backed by
matching exact-head journal metadata, marker and label. Preserve manual values,
gates and dependencies. Report terminal lifecycle without changing status.

Keep repository handoffs authoritative for task coordination and acknowledgments.
Project fields are derived views. Cursor proposals identify observations by
repository, PR, head, intended owner and handoff blob revision; they are not
delivery receipts or distributed locks.

## Alternatives Considered

- A workflow in every repository: deferred to avoid repeated configuration and
  calls before a central dry run has been evaluated.
- Native Project auto-add only: useful discovery but insufficient for durable
  handoff verification, archived deduplication and ownership conflicts.
- Immediate apply or autonomous implementation: deferred because authentication,
  live coverage, field provenance and concurrency/recovery need separate proof.
- A mandatory task database or schema: rejected for the core convention; the
  example's explicit JSON input is adapter data, not a migration requirement.

## Rationale

A deterministic, bounded proposal is reviewable and testable without changing
GitHub or depending on private agent conversations. Explicit allowlists and
fail-closed reads make missing access visible. The existing Markdown convention
and optional coordination protocol remain usable without this adapter.

## Consequences

The example requires a source checkout; installed initializer behavior and
packaged resources remain unchanged. Tests prove offline planning and guarded
collection with controlled responses, not production readiness. Plans can
become stale immediately. No atomic exactly-once guarantee is claimed.

Apply remains deferred until independently reviewed authentication, actual live
reads, per-field provenance, current-state rechecks, restart/duplicate tests
and reversal of controller-owned changes are demonstrated. Scheduling and
external writes require their own explicit scope.
