# Session: Writer readback diagnostic investigation

Date: 2026-11-04

## User Goal

Investigate a supervised single-item pilot's needs_review anomaly using immutable
original evidence and current code. Distinguish proof from hypotheses, preserve
fail-closed behavior, prepare a reviewable diagnostic PR if justified and define
measurable next-pilot criteria. No repeated mutation, credential/schedule changes
or direct Project item writes are authorized by this investigation.

## Investigation

Main/source `451c7c8c9315a59fdff838e37d6f9b6b80e1b5c6`, clean baseline85 tests.
Original private receipt hashes validate. The journal shows prepared, intent,
acknowledged, needs_review and later reconciled; no complete event. The immediate
exception and snapshot were not retained. Its precise triggering predicate cannot
be demonstrated from those receipts. Exact private timeline/state comparisons
remain outside this public repository.

The catch-all post-ack handler includes read/normalization, preservation and
target identity/archive checks. It discarded all exception information. Aggregate
six-read/120-point telemetry rules out configured call/page-cap exhaustion but
not page/data inconsistencies, a rate-floor guard or state/identity verification.
Two distinct synthetic transients reproduce the same aggregate and later success,
demonstrating that metrics alone do not identify a root cause. Native defaults
alone are permitted and therefore are not an explanation.

## Decisions

Add sanitized observational metadata only: fixed code and verification stage,
bounded page counts/rate evidence/fingerprints and complete normalized state when
available. No raw exception/transport data, partial-state acceptance, retries,
scope change or automatic promotion of an uncertain receipt. Old schemas remain
readable; original receipts are never rebuilt or changed.

## Changes Made

Added writer_diagnostics.py, bounded Backend read evidence, additive needs_review
diagnostics/observed-state capture,13 focused offline tests, operator diagnostic
guide, ADR0006 supplement and current context. The collector, installed core,
mutation transport and workflows retain their behavior. Work is in the task-owned
isolated checkout on a dedicated branch.

## Tests

RED tests demonstrated missing classifications/evidence. Final98 tests pass with
checkout-local src imports. Two generic45-item paginated cases each produce
exactly6 reads/120 points/one mocked add, then read-only recovery with no resend.
Tests cover timeout/access/JSON/rate evidence, changed originals, invisible target,
mismatched/archived acknowledgment target, unknown exception privacy and receipt
failure/spent replay. Existing85 tests pass unchanged. No test uses live GitHub.

Independent review reproduced classification precedence losing scope/JSON detail;
fixed with RED/GREEN regression. Reviewer independently passed98 tests, malformed
evidence/privacy/page-bound fault injections and whitespace checks, finding no
remaining actionable implementation issue. Documentation/CI evidence is completed
by the author and recorded in the draft PR.

## Problems Encountered

Historical failure cause remains unknown because the failing observation was lost.
Shared bucket counters and missing per-page traces prevent reconstructing exact
rate/pagination history. No current API query could recover past state; none was
made for this investigation. Without PYTHONPATH=src a separate installed package
can mask checkout resource provenance; all reported runs use the checkout.

## Current Result

Diagnostic fix reviewed/tested, fail-closed semantics preserved. Historical
needs_review remains unchanged; later successful reconciliation is separate
evidence. This is readiness for a diagnostic PR, not pilot or unattended approval.

## Next Steps

Review exact PR head and natural CI. Prefer the diagnostic revision before another
separately approved absent-target pilot; do not repeat the old operation. Require
one attempt, complete preservation, clean receipt or fully explained safety stop,
sanitized trace and independent readback per PROJECT_WRITER_DIAGNOSTICS.md.
