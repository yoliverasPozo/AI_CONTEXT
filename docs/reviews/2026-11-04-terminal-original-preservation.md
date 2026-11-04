# Independent terminal preservation review

Base: merged main `c4d9fa2ae8d85fc99befdddc787bd9f4aa3edf19`.
Scope: the corrective working-tree diff on `fix/project-readback-stabilization`,
including the terminal guard, synthetic test, writer/ADR/context/session changes
and review-gate investigation. Final commit and CI are tracked in the PR.

A separate reviewer agent inspected the implementation and documentation without
editing files or using remote APIs. No actionable findings were returned.

Independently verified:

- Terminal subset check precedes retryable count-change failure and covers
  approved archived originals.
- Active/archived omission cases stop at the first read attempt, preserve durable
  [4,3] count evidence, never complete and cannot regain a mutation attempt.
- Existing malformed-count guards remain non-retryable even if they run before
  the new subset guard; no requirement to relabel those failures was introduced.
- Sixteen focused stabilization tests and all118 offline tests pass, import
  provenance points to checkout-local `src`, and whitespace validation passes.
- Gate proposal distinguishes completion, disposition and merge authorization;
  no enforcement implementation or live setting change is claimed. The reviewer
  checked supplied timing/protection evidence for consistency, not independently
  against GitHub.

Implementer verification independently passed29 focused stabilization/diagnostic
tests and all118 tests. The original merged-main regression first failed for
both new subcases with actual verified_present instead of required needs_review.
This is offline evidence, not a live pilot or unattended-operation acceptance.
