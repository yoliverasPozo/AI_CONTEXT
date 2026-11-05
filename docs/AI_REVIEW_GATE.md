# AI review completion gate

The optional evaluator observes open, non-draft PRs from this repository into
`main`. Its CLI prints a decision and a sanitized receipt. A passing receipt
is a candidate for the future `AI review complete` status. Merge approval
continues to come from the owner.

```powershell
python -m examples.review_gate --pr 8
python -m unittest tests.test_ai_review_gate -v
```

Run the CLI from a trusted checkout with the installed GitHub CLI on a trusted
PATH and an existing GitHub login. Exit 0 means the observation passed the
current evidence policy. Exit 1 means it blocked. Output contains fixed reason
codes, repository and PR identity, call count and, on success, the full head,
base tip, evidence IDs and SHA-256 digests. Comment bodies, API errors and
credentials stay out of the receipt. The CLI has no publication switch.

## Verified GitHub signals

The repository is public, on GitHub Pro. On November 5 `main` pointed to
`810a7388e1989558e1e787a81cd66d19c6fa21c8`. GitHub reported
`protected: false`, the classic protection endpoint returned “Branch not
protected,” and the repository rulesets list was empty. Default Actions
permissions were read and Actions review approval was disabled.

| Source | GitHub identity | Required evidence |
| --- | --- | --- |
| Codex | App `1144995`, bot `199175422` | One authenticated summary with a version 1 code review record for the full head SHA, completed and both findings flags false. An active security review must also be current and clean. |
| PR Lens | App `4690539`, bot `320153949` | One authenticated sticky comment with a current full SHA and PR-specific graph key, a clean review section, and a retained bot edit showing the review pending for that full SHA immediately before the clean result. One matching successful PR Lens check must link to the sticky comment and match the pending edit's timestamp. |
| Tests | GitHub Actions App `15368`, workflow `347167039` | The latest matching `pull_request` run for this head and branch is successful. All four expected jobs come from that run's suite. The workflow blob matches the current main tip. |
| Conversations | GitHub GraphQL for the same PR and head | Every inline thread resolved, a complete review list and no blocking review decision. Separate same-head submissions from either bot block until disposition can be proven. |

PR #13 showed an unresolved Codex finding and a successful PR Lens check.
PR #14 showed the transition from that distinction to a clean re-review on
`14462400e74da5185094a221ba53704a21ffd68d`. On November 5 Codex finished at
12:53:50 UTC. PR Lens's check succeeded at 12:54:40 UTC with output
`Lenses rendered`, while the comment still said it was reviewing. Its clean
review appeared at 12:59:33 UTC. A push had first marked the prior drawing
outdated. A one-time redraw request started the new review. Codex started
automatically on the push. [PR #13 evidence](2026-11-04-review-completion-gate.md)
· [PR #14 Codex](https://github.com/yoliverasPozo/AI_CONTEXT/pull/14#issuecomment-6640061538)
· [PR #14 PR Lens](https://github.com/yoliverasPozo/AI_CONTEXT/pull/14#issuecomment-6640059470)
· [PR #14 CI](https://github.com/yoliverasPozo/AI_CONTEXT/actions/runs/42030858201)

The existing `AI_CONTEXT handoff inbox` workflow reconciles advisory labels on
same-repository PRs using `pull_request_target`. The gate ignores labels and
handoff markers. A routing event or check cannot supply review evidence.
[Handoff protocol](COORDINATION.md)

## Trust and findings disposition

The collector joins REST App and bot IDs to the same GraphQL comment node,
body and timestamps. It requires the original author and every visible
editor to be the pinned bot. A minimized comment, unexpected editor, deleted
edit, duplicate marker, truncated response or missing field blocks. On the
observed PR Lens history, GraphQL's `diff` returned the full raw body of each
revision. The evaluator requires that shape and rejects an observed collision
between the abbreviated SHA and a different full SHA in the retained history.
An editable Markdown body alone provides no proof of identity or review.
These provider formats are empirical and can change. The publisher must stay
inactive until an exact-head review contract or authenticated attestation has
been validated. [GitHub comment schema](https://docs.github.com/en/graphql/reference/issues#issuecomment)

The implemented disposition path is a clean, authenticated re-review on the
current revision plus resolved inline conversations. An unresolved finding
blocks even if its thread is marked resolved. A current-head standalone
bot review blocks because its findings may arrive before the sticky summary
changes. Prior-head bot submissions can coexist with a clean current review
after their conversations are resolved. The evaluator grants no text-based
waiver. A future waiver or reviewer attestation needs an authenticated,
allowlisted reviewer ID and an auditable record of repository, PR, head, base
or diff, evidence digest, finding IDs and individual decisions. A retained
append-only ledger would detect changes or removals after the first observation.
The GitHub snapshot cannot recover findings deleted before observation.

## Publication boundary

Tests inject a publisher into `reconcile` and validate the fixed commit-status
request from `commit_status`. The protocol sends pending before evaluation,
re-reads all the evidence, compares its digest and checks the PR scope again
immediately before success. A failed read, changed digest or transport error
returns a blocked result. If the pending request succeeded, it stays pending
when evaluation fails. The read-only CLI also rechecks PR scope before
reporting eligibility. The request contains a fixed context and a digest
reference. A future trusted host must retain the full receipt alongside it.
[GitHub commit status API](https://docs.github.com/en/rest/commits/statuses)

Production publication needs a dedicated GitHub App identity with installation
scope limited to the pilot repository and the minimum permissions for metadata,
PR/issue/Actions/check reads, workflow blob reads and commit statuses write.
Keep the private key or token in a separately protected host or environment.
Use trusted code and an installed, pinned GitHub CLI or fixed API client.
The GitHub Actions App identity is shared by workflows. Pinning it alone cannot
distinguish a same-name check produced by a changed PR workflow. The observer
checks the canonical workflow run and suite for CI. Use the dedicated App as
the source of the aggregate status. It needs no merge, Project or repository
administration permission.

GitHub stores a required status against a commit, so a different PR with the
same SHA can inherit it. The observer refuses currently ambiguous open heads,
but a later PR, reopened PR or force reset can reuse a previously green SHA.
Similarly, edits, dismissals, CI reruns and missed webhooks can invalidate
evidence while the head remains fixed. A recheck reduces the race window.
GitHub provides no atomic operation that reads the reviewer evidence, publishes
a status and merges. Before any required rule is enabled, prove a controlled
head reuse policy and status invalidation in a sandbox. If that cannot be
established, keep the status advisory and require a fresh observation at the
human merge decision.

## Events and cost

The event selector is a pure function exercised with synthetic deliveries.
It deduplicates PR numbers in a batch and ignores handoff labels, generic PR
description edits, human conversation comments and its own status events.
Event hints select a PR for fresh reads. They carry no authorization or review
result. No workflow consumes these events in this PR.

| Candidate event | Purpose and delivery gap |
| --- | --- |
| PR opened, synchronize, reopened, draft change, base edit or close | Invalidate or reevaluate scope. A future publisher must also revoke an existing success when a PR leaves scope. |
| Reviewer `issue_comment` created, edited or deleted | Catch terminal results and same-head changes. Use the original comment author for filtering an edit or deletion, then fetch fresh evidence. |
| Review submissions, comments and thread changes | Detect findings, dismissal and resolution. `pull_request_review_thread` is a webhook event without a native Actions trigger. Native conversation resolution helps, with manual refresh or an App for delivery gaps. |
| Third-party `check_run` completion | Optional wake-up. Actions suppresses some check events when the check suite or SHA is associated with Actions. Verify delivery before using it. |
| Existing Tests `workflow_run: completed` | Wake the trusted observer for CI. PR association arrays were empty on the sampled PR #14 API records. Use a bounded lookup by repository, head and branch, or manual dispatch when association cannot be proven. |

Use a single trusted default-branch entry point, scope event filters by app and
workflow, and serialize any future publication by repository, SHA and context.
Coalesce bursts and retain a trailing refresh when an event arrives during an
evaluation. Compare a receipt digest before redundant writes. A missed or
out-of-order event must never substitute for a fresh check. GitHub generally
suppresses workflow recursion from `GITHUB_TOKEN`, with dispatch exceptions
and approval-gated PR workflow runs for certain PR changes. Do not depend on
that behavior for deduplication. A manual observer is the first pilot. A
trusted Actions runner can host the observer without a new service. Add an App
event relay only if delivery and isolation tests justify the operational cost.
[Actions events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
· [GITHUB_TOKEN](https://docs.github.com/en/actions/concepts/security/github_token)
· [Review thread webhook](https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request_review_thread)

The live read of PR #8 took about six seconds on Windows and used nine API
requests. A passing observation adds two scope reads. Simulated publication
uses two complete reads and two scope checks, normally 22 API reads before
success. The pending write follows the first scope check. The CLI caps a session
at 24 calls and 30 seconds. It bounds REST
pages and refuses truncated GraphQL connections rather than guessing. No new
Actions run is created by the observer today. An illustrative rollout at five
one-minute Linux jobs per PR and 20 PRs per month would consume about 100
runner-minutes per month, including provisioning. Measure real counts and
latency in a sandbox. Standard hosted runners are free for this public
repository. [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)

## Proposed GitHub Pro ruleset

Apply a repository branch ruleset to `refs/heads/main` only after the publisher
and delivery tests pass. Require a PR, resolved conversations and up-to-date
required checks. Block force pushes and deletions. Leave ordinary bypass
actors empty. Require the four contexts below from GitHub Actions App
`15368` and `AI review complete` from the dedicated publisher's verified App
ID. Require the PR Lens check from App `4690539` as an additional native
signal if the sandbox confirms the check association. Human merge approval
remains a separate step. [Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)

- `test (ubuntu-latest, 3.10)`
- `test (ubuntu-latest, 3.13)`
- `test (windows-latest, 3.10)`
- `test (windows-latest, 3.13)`

The observer checks reviewer evidence on the PR head. CI evidence ties the
checks to that head's existing workflow suite. It does not prove that suite
tested the latest base tree. `pull_request` Actions may run on a synthetic
merge commit, and GitHub can require results on that commit where it has
statuses. Verify the Checks and merge box behavior for the exact rule in the
sandbox. Record head, current target tip and tested merge SHA. Test advances
of main, PR retargeting, same-head reopen and duplicate heads before applying
strict required checks. A synthetic merge commit has no documented per-PR
identity guarantee. [Required-check troubleshooting](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)

## Recovery and approvals

If the observer blocks, use its reason code to inspect the relevant current
review, CI run, conversation or API access. Refresh after fixing the source
evidence. A provider shape change needs new fixtures and review. For a
publication timeout or lost response, inspect the status as the expected App
before any retry. Treat an unavailable publisher or stale evidence as a merge
hold. Future activation should retain the previous ruleset configuration and
status source. To roll back, pause merges and remove only the new requirement
with owner approval before disabling the publisher. Preserve native CI and
conversation rules and the evidence receipts.

Separate approvals cover merging the reviewed implementation, enabling a
non-enforcing sandbox publisher and its minimal App credentials, and applying
the final ruleset to main after sandbox evidence. Any event wiring or protected
environment for publication belongs to that rollout. The existing repository
and Project workflows are outside the gate's scope.
