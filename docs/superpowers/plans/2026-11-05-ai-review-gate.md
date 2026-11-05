# AI review gate implementation plan

Build a repository-specific adapter with Python 3.10 and the standard library.
Keep the existing checkout isolated on a feature branch. The gate CLI uses the
existing GitHub CLI session for read-only observation.

- Capture API shapes and numeric reviewer identities from PRs 13 and 14.
- Test reviewer states, tampered provenance, stale head, incomplete reads, CI
  identity, review conversations, event filtering and duplicate notifications.
- Implement strict evidence parsing and the bounded GitHub reader. Return a
  sanitized decision and an evidence digest.
- Simulate publication with an injected transport. Re-read evidence and the PR
  identity before a success. Keep credential wiring and workflow activation
  outside this PR.
- Review the trust boundaries and test the normal CLI against open PR data.
  Document event delivery, cost, native rules, rollback and rollout blockers.
- Run the full suite and independent security review. Open a draft PR.
