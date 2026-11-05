# Decision: Authenticate review evidence before enabling a merge gate

## Status

Experimental. Observation and simulated publication.

## Context

PR #13 merged while Codex was still reviewing. PR #14 showed that PR Lens can
finish its drawing check several minutes before completing review. GitHub
required checks apply to commits, and reviewer evidence can change on the
same commit.

## Decision

Use an optional repository-specific observer on trusted code. Require current
authenticated Codex evidence and its provenance, verified CI and resolved
conversations. [ADR 0009](0009-documentation-skip-and-sandbox-status.md)
specifies advisory PR Lens evidence and disposition of known findings. Record a bounded receipt and exercise pending and success
publication against a simulated transport. Keep the publisher and native
rules inactive pending an owner-approved sandbox validation.

## Alternatives Considered

- Require CI and a PR Lens check alone. This leaves both Codex completion and
  PR Lens review disposition unverified.
- Treat review text, labels or resolved threads as authorization. Editable
  comments and provider races make these incomplete signals.
- Add a dedicated continuously running service. Event delivery and publication
  isolation might eventually justify one. A manual observer can validate the
  evidence contract first.

## Rationale

Separate eligibility, publishing and human merge authority. Use numeric App
and bot IDs plus edit provenance and a fresh head. A production App publisher
needs verified status source, shared-SHA isolation and an invalidation plan.

## Consequences

The observer blocks when required evidence is incomplete or known findings
remain unresolved. The existing Actions and handoff workflow stay outside
the gate. Native status rules cannot atomically reflect mutable review evidence
and do not identify a specific PR for a shared SHA. See the
[operating guide](../AI_REVIEW_GATE.md) for activation prerequisites.
