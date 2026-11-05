# Decision: Keep PR Lens advisory and bind disposition to known findings

## Status

Experimental. Follow-up to [ADR 0008](0008-review-gate-observation.md).

## Context

PR #16 received an authenticated PR Lens documentation skip without a commit
SHA. Its changes included agent instructions and coordination rules. PR #17
received a successful drawing check without a terminal review verdict or
intentional skip. GitHub commit statuses are visible across PRs sharing a head
and may remain green after review evidence changes.

## Decision

Require an authenticated, completed current-head Codex review with no
unresolved findings, all required CI and resolved conversations. Treat PR Lens
as advisory across all change classes. Report skip, incomplete and unknown
evidence separately from an authenticated clean review.

Verified unresolved findings still block. Retain findings from authenticated
history available to the evaluator. Clear them with verified re-review
evidence or a formal, unedited owner disposition binding the exact PR, head,
base, complete immutable diff and known findings. Maintain the distinction
between ordinary documentation, sensitive documentation and executable or
mixed changes in the disposition evidence.

Model publication and PR-specific receipts in memory with a dedicated
simulated identity. Merge, auto-merge, deployment and bypass require separate
explicit owner authorization.

## Alternatives Considered

- Require a terminal PR Lens verdict or intentional skip. The observed
  provider can complete rendering without either outcome.
- Infer a clean review from successful rendering or silence. Neither proves
  review completion or clears a known finding.
- Treat a dedicated App's native success as PR-specific. Other PRs referencing
  the same SHA can inherit the status.

## Rationale

Required Codex and CI evidence remains fail-closed. Review findings remain
actionable even when the advisory provider's terminal verdict is missing.
A fresh observation and a separate owner decision avoid depending on cached
native green.

## Consequences

Unknown or incomplete PR Lens evidence is reported as advisory. Incomplete
diff proof prevents disposition of known findings. GitHub cannot recover
evidence deleted before observation. A live sandbox requires validation of
durable findings receipts, event delivery, status source and recovery under
separate approval. See the [operating guide](../AI_REVIEW_GATE.md).
