# Session: Terminal original-item preservation and merge review gate

Date: 2026-11-04

## User Goal

Prepare a third supervised pilot after PR13, then incorporate Codex's P2 finding:
terminal pagination-count mismatch must not restart if any approved original is
missing. Investigate a gate that waits for Codex and PR Lens before merge. No live
Project writes, merges, credential expansion or recurring automation changes.

## Investigation

PR13 merged at `c4d9fa2ae8d85fc99befdddc787bd9f4aa3edf19`, with the same tree as
reviewed `4d4a793`; all four exact-main test jobs passed (run41892331064), and
117 local tests passed before correction. Private read-only reconciliation found
no eligible missing PR; no proposal, operation ID, digest or expiry was created.
Operational inventory and calibration evidence remain outside this public repo.

Synthetic count4-to3 terminal omission followed by stable read reproduced
`verified_present` on merged main for active and archived approved originals.
Per-item validation could not detect absent items; the typed count exception
skipped final preservation checks before restarting.

Public review/check timestamps establish Codex finished after merge. Main has
no observed branch protection or repository rulesets. See the
[gate investigation](../reviews/2026-11-04-review-completion-gate.md) for evidence,
limitations and a separately gated enforcement proposal.

## Decisions

Check all approved original IDs at terminal pages before restart eligibility.
Keep count overflow/incomplete-page checks fatal; no broad retry or mutation
retry. Reuse the existing stabilization branch, with a new corrective draft PR.
Investigate and document the review gate; do not activate it or add workflows.

## Changes Made

- Reader: terminal subset guard uses the existing sanitized original_item_changed
  classification; field-ID set computed once per page.
- Synthetic regression: active and archived original omission, one attempt,
  durable [4,3] count evidence, no complete event or later promotion.
- Writer documentation/ADR clarify terminal omission precedence.
- Current context, implementation plan and review-gate investigation synchronized.

## Tests

RED: new regression failed for both subcases on merged-main implementation:
actual verified_present, required needs_review. GREEN: 29 focused stabilization/
diagnostic tests passed. Full suite and independent reviewer both passed118
tests; correct import provenance was checked. Whitespace validation passed.
Exact corrective PR head and CI evidence will be reported with publication.

## Problems Encountered

No genuinely absent open PR was found; a timed pilot proposal would be invalid.
Review completion metadata is integration-specific and not a documented stable
GitHub contract. A real trusted evaluator and event-race tests are still needed.
One private audit subprocess used Windows' default cp1252 and failed decoding
Unicode PR text; explicit UTF-8 fixed the read-only audit. No source fix needed.
An import-provenance assertion also rejected the installed package before tests
ran; explicit PYTHONPATH=src corrected the probe and the saved full-suite run.

## Current Result

Corrective implementation ready for review; experimental stabilization remains
disabled by default. Both historical pilot operation inventories remain unchanged
(53 files). No writer enablement, proposal preparation, live mutation, review
request, repository rule change, schedule activation or merge was performed.

## Next Steps

Review the corrective draft PR and both integration reviews on its final head.
After a separately authorized merge, recheck main/CI and reconcile for an eligible
absent open PR; only then prepare a fresh timed proposal and stop for operation-
specific approval. Review-gate implementation/activation require separate scope.
