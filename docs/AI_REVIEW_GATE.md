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
| PR Lens | App `4690539`, bot `320153949` | An authenticated current-head clean review and matching drawing check, or a verified documentation skip with a current owner disposition. |
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

For an actual review, require a clean, authenticated re-review on the current
revision plus resolved inline conversations. The sticky comment must bind the
pending-to-clean history to the full head and PR-specific graph key, and its
drawing check must link to the comment and match the pending edit's timestamp.
An unresolved finding
blocks even if its thread is marked resolved. A current-head standalone
bot review blocks because its findings may arrive before the sticky summary
changes. Prior-head bot submissions can coexist with a clean current review
after their conversations are resolved. The documentation skip described below
does not waive findings. Any future finding waiver needs its own authenticated
scope and individual finding IDs. A retained
append-only ledger would detect changes or removals after the first observation.
The GitHub snapshot cannot recover findings deleted before observation.

## Intentional documentation skips

PR #16 changed 11 files, including agent instructions, packaged instructions,
and the coordination guide. PR Lens posted an unedited skip notice without a
SHA and created no check on that head. Codex completed a clean review and all
four CI jobs passed. Historical replay with a simulated open scope and the
pre-merge target tip classified the actual diff as sensitive documentation
and required an owner disposition. The merged PR remains outside live scope.
[PR Lens notice](https://github.com/yoliverasPozo/AI_CONTEXT/pull/16#issuecomment-6660777168)
· [Codex review](https://github.com/yoliverasPozo/AI_CONTEXT/pull/16#issuecomment-6660779756)

For the exact observed notice, the observer verifies App, bot, original body
and provenance. Edited notices, additional authenticated PR Lens comments
and contradictory checks or submissions block. It reconciles the paginated
PR file list with the immutable head and merge-base trees for the current
target tip. Counts, paths, both rename endpoints, blob IDs and modes must agree.
Truncation or unsupported metadata blocks. The most restrictive category
applies across the entire diff.

| Change class | Skip treatment |
| --- | --- |
| Ordinary documentation | Regular Markdown blobs at the reserved release-note paths `CHANGELOG.md` and `docs/release-notes/vX.Y.Z.md`. The owner confirms the content and binds the unversioned notice to this diff. |
| Sensitive documentation | Other regular Markdown, including agent instructions, operational and security guidance, and gate policies. The owner reviews security and authority effects and records the reason for accepting the skip. |
| Executable or mixed | Code, workflows, configuration, other file types, executable modes, symlinks and submodules require the full review path. |

The path and mode checks establish where and how a file is stored. The owner
reviews the content, including any security instructions placed in an otherwise
ordinary path. Both eligible skip classes require clean Codex, CI and resolved
conversations on the current head.

When the observer returns `pr_lens_skip_requires_disposition`, the pinned
repository owner can inspect the diff, notice and evidence. If the owner accepts
the exception, submit a GitHub review with **Comment** on that head. Include a
short rationale and a single marker on its own line containing the exact JSON
from `evidence.disposition_request`.

```text
<!-- ai-review-gate-disposition:v1 { ... exact JSON from the observer ... } -->
```

The observer checks the current repository owner's numeric User ID, the
review commit, submission time and unedited provenance. The disposition binds
the PR, target branch, full head, base tip, merge base, class, file digest,
notice ID and notice digest. A new disposition can supersede an older one when
main advances. Duplicate current dispositions block. This is a human exception
for an authenticated, unversioned notice. It grants no merge authority and
carries no claim that PR Lens reviewed the SHA.
[Review schema](https://docs.github.com/en/graphql/reference/pulls#pullrequestreview)
· [PR files](https://docs.github.com/en/rest/pulls/pulls#list-pull-requests-files)
· [Git trees](https://docs.github.com/en/rest/git/trees#get-a-tree)

## Publication boundary

The disabled-by-default `SandboxPublisher` is an in-memory transport. It
records pending, success and failure requests with a simulated App ID,
generation, full PR scope, decision, evidence and digest. A success requires
two consistent evidence reads and a final scope recheck. A known blocker in
the same scope can emit failure. Scope drift and unexpected failures can
leave pending. Simulated acknowledgement loss can leave a visible success
without a confirmed receipt. The read-only CLI has no publication switch and
rechecks scope before emitting eligibility or a disposition request.
[GitHub commit status API](https://docs.github.com/en/rest/commits/statuses)

For a future pilot, separate the trusted reader from a dedicated status
publisher App installed only in the sandbox repository. The publisher needs
Metadata read and Commit statuses write. The reader needs access to PRs and
associated comments, Actions runs, checks and Git content. Verify the smallest
grant and the actual status source during sandbox acceptance.
Keep the private key or token in a separately protected host or environment.
Use trusted code and an installed, pinned GitHub CLI or fixed API client.
The GitHub Actions App identity is shared by workflows. Pinning it alone cannot
distinguish a same-name check produced by a changed PR workflow. The observer
checks the canonical workflow run and suite for CI. Use the dedicated App as
the source of the aggregate status. It needs no merge, Project or repository
administration permission.

GitHub stores a required status against a commit, so a different PR with the
same SHA can inherit it. The observer refuses currently ambiguous open heads,
and the simulator refuses a second PR's claim on a head it has seen. GitHub
can still expose the first PR's green status. The observer blocks recorded
reopen, retarget, conversion to draft, head restoration and head or base
force-push history. Use a manual review or new PR and revision in these cases.
An initially Draft PR can become Ready for Review.
Similarly, edits, dismissals, CI reruns and missed webhooks can invalidate
evidence while the head remains fixed. The simulator fences older terminal
writes and invalidates local receipts, even when native green remains visible.
A recheck reduces the race window. Lost local state or missed events can
still leave a stale status.
GitHub provides no atomic operation that reads the reviewer evidence, publishes
a status and merges. Keep the status advisory. The safer fallback is an
owner-controlled merge decision after a fresh trusted observation of the
exact PR, head and target tip, with separate human authorization. A merge API
SHA guard can reject a moved head. It cannot pin mutable review evidence.
[Merge API](https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request)

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

The normal observation uses nine reads plus two for a passing scope recheck.
The skip adds five diff reads. The PR #16 replay used 16 reads including the
scope recheck. A future publication cycle would use about 22 reads for a
full review or 32 for a skip, plus status writes. The existing 24-call and
30-second CLI budget covers observation. A skip publication cycle needs a
separately validated read budget. Publication tests use synthetic evidence.
Cap and coalesce writes below GitHub's per-SHA/context limit. Treat exhausted
revocation capacity as a hold.

| Architecture | Operational and compute tradeoffs |
| --- | --- |
| Trusted Actions job | No daemon. Use default-branch code, filtered events and no PR execution. At 20 heads per month and three to five short jobs per head, estimate 60 to 100 one-minute runner slots including setup. Verify check and thread event delivery. |
| Dedicated App | Independent status source and webhook delivery. Requires installation, key custody, deduplication and a receipt store. Hosting adds cost and cannot remove native SHA reuse. |
| Manual observation and attestation | One fresh observation at the owner's decision. Uses the existing session and zero new Actions jobs. Requires operator time and a separate merge decision. |

Standard hosted runners are free for this public repository. The table models
usage and is not a billing prediction for other repositories.
[GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)

## Proposed GitHub Pro ruleset

Apply a repository branch ruleset to `refs/heads/main` only after the publisher
and delivery tests pass. Require a PR, resolved conversations and up-to-date
required checks. Block force pushes and deletions. Leave ordinary bypass
actors empty. Require the four contexts below from GitHub Actions App
`15368` and `AI review complete` from the dedicated publisher's verified App
ID only if strong enforcement is demonstrated. An unconditional native
PR Lens check would strand skips with no check. Keep its disposition inside
the aggregate evaluator. Human merge approval
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

For the first live sandbox proposal, identify one disposable repository,
target branch, PR, full commit SHA, context and dedicated App installation.
Review the sandbox-specific adapter and its read budget. Request approval for
one pending/success pair and one pending/failure pair at most. Keep the context
advisory. Use a second PR with the same SHA to observe native status reuse, and
capture provider identity, readback and both PR-specific receipts. Test a
withheld event and simulated lost acknowledgement without authorizing a merge.
If any write outcome is uncertain, stop, inspect the status source and retain
the evidence before asking about recovery. These are preparation steps for a
separate authorization.
