# Decision: Verify documentation skips and keep commit statuses advisory

## Status

Experimental. Follow-up to [ADR 0008](0008-review-gate-observation.md).

## Context

PR #16 received an authenticated PR Lens documentation skip without a commit
SHA. Its changes included agent instructions and coordination rules. GitHub
commit statuses are visible across PRs sharing a head and may remain green
after review evidence changes.

## Decision

Match the bounded PR files list against immutable Git trees before considering
a skip. Classify reserved release notes separately from sensitive documentation
and executable or mixed changes. Bind unversioned notices to the current
scope through a formal, unedited disposition from the pinned owner. Require
clean Codex, CI and resolved conversations throughout. Model publication and
PR-specific receipts in memory with a dedicated simulated identity.

## Alternatives Considered

- Accept the documentation notice based on file extensions. This cannot
  distinguish a symlink, executable mode, policy or incomplete file list.
- Require the PR Lens check on every PR. Intentional skips may emit no check.
- Treat a dedicated App's native success as PR-specific. The publisher identity
  controls who writes the status. It does not control which PR inherits it.

## Rationale

The owner disposition binds a real skip notice to verified current evidence
without claiming PR Lens reviewed that revision. A fresh manual observation
and separate owner merge decision provide a safer interim route than relying
on cached native green.

## Consequences

The observer blocks uncertain file lists, unsupported notices, reused lifecycle
states and unverified dispositions. The sandbox must validate event delivery,
status source and recovery under separately approved scope. See the
[operating guide](../AI_REVIEW_GATE.md).
