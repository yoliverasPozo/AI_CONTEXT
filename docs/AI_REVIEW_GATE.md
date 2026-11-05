# AI review completion gate

The optional evaluator observes open, non-draft PRs from this repository into
`main`. Its CLI prints a decision and a sanitized receipt. A passing receipt
is a candidate for the future advisory `AI review complete` status. Merge approval
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
| Codex | App `1144995`, bot `199175422` | One authenticated summary with a version 1 code review record for the full head SHA, completed, with no unresolved findings. An active security review must also be current and clean. |
| PR Lens | App `4690539`, bot `320153949` | Advisory. A verified unresolved finding blocks. An absent, incomplete or stale verdict leaves PR Lens advisory and does not block by itself. |
| Tests | GitHub Actions App `15368`, workflow `347167039` | The latest matching `pull_request` run for this head and branch is successful. All four expected jobs come from that run's suite. The workflow blob matches the current main tip. |
| Conversations | GitHub GraphQL for the same PR and head | Every inline thread resolved, a complete review list and no blocking review decision. Unverified same-head standalone Codex submissions block. Verified PR Lens findings are tracked separately from thread resolution. |

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

## Review evidence and findings

Codex, all four required CI jobs and resolved conversations are mandatory.
The collector joins the reviewer App and bot IDs to the corresponding GitHub
GraphQL node, body and timestamps. Codex requires complete, unambiguous proof
on the full head. A missing Codex comment blocks. A minimized comment,
unexpected editor, duplicate marker or incomplete required history cannot
satisfy the proof.

PR Lens is advisory for ordinary documentation, sensitive documentation and
code changes. The receipt distinguishes authenticated clean review,
intentional skip, incomplete review, unknown evidence and known findings.
An intentional skip such as [the notice on PR #16](https://github.com/yoliverasPozo/AI_CONTEXT/pull/16#issuecomment-6660777168)
conveys that the provider skipped. A successful drawing check, silence or a
prior-head verdict cannot establish a clean current review. An authenticated
clean verdict must bind the PR-specific pending-to-clean history to the full
head and a matching drawing check. Provider formats are empirical and can
change. [GitHub comment schema](https://docs.github.com/en/graphql/reference/issues#issuecomment)

The evaluator checks authenticated finding reports in issue comments,
standalone reviews and inline review comments. It considers retained
bot-authored versions even when a report was edited, minimized or dismissed.
A resolved thread alone does not clear a verified finding. A verified clean
current-head review can supersede reports strictly older than its authenticated
pending marker. Reports during or after that review remain blockers. GitHub
review decisions and unresolved threads remain independent blockers. A GitHub
snapshot cannot recover a finding deleted before observation. A live pilot
needs a durable evidence ledger to retain previously observed blockers.

## Owner disposition of known findings

Address the finding and obtain verified clearing evidence, or have the owner
review and explicitly disposition the exact known findings. The observer
reconciles the complete PR file list against immutable head and merge-base
trees for the current base tip before offering a disposition. Counts, paths,
rename endpoints, blob IDs and modes must agree. The request records whether
the diff is ordinary documentation, sensitive documentation, or executable or
mixed. Only regular Markdown at reserved release-note paths qualifies as
ordinary documentation. The classification records scope for human review
and grants no automatic waiver.

When the observer returns a finding blocker with
`evidence.disposition_request`, the pinned repository owner can submit a
GitHub review with **Comment** after inspecting the findings and the exact
diff. Use the following paragraphs without the surrounding code fence.

```text
I disposition the recorded PR Lens findings for this revision.

<!-- ai-review-gate-findings-disposition:v1 { ... exact JSON from the observer ... } -->

<Explain the resolution or risk accepted for each recorded finding>
```

The review must be unedited, on the exact head and submitted strictly after
each recorded finding. Timestamps must include explicit timezones and are
compared as instants. The request binds the PR, target branch, full head, base
tip, merge base, diff classification and digest, plus the finding source IDs,
timestamps and digests. A changed scope or new finding needs fresh evidence.
Duplicate current dispositions block. This records the owner's treatment of
the known findings. Merge, auto-merge, deployment and bypass each require
separate explicit authorization.
[Review schema](https://docs.github.com/en/graphql/reference/pulls#pullrequestreview)
· [PR files](https://docs.github.com/en/rest/pulls/pulls#list-pull-requests-files)
· [Git trees](https://docs.github.com/en/rest/git/trees#get-a-tree)

## Publication boundary

The disabled-by-default `SandboxPublisher` is an in-memory transport. It
records pending, success and failure requests with a simulated App ID,
generation, full PR scope, decision, evidence and digest. A success requires
two consistent evidence reads and a final scope recheck. The simulator reserves
its invocation generation before the first scope read. Older invocations
cannot publish after a newer invocation starts. A known blocker, including a
missing required Codex comment, emits failure after a stable scope recheck.
Scope drift and unavailable or unexpected read failures can leave pending. Simulated acknowledgement loss can leave a visible success
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
A known finding can add five diff reads to prepare a disposition. A future
publication cycle would use about 22 reads for a normal observation or 32
when verifying a disposition, plus status writes. The existing 24-call and
30-second CLI budget covers observation. A disposition publication cycle
needs a separately validated read budget. Publication tests use synthetic evidence.
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
ID only if strong enforcement is demonstrated. Keep PR Lens advisory and verify known findings in the aggregate evaluator. Human merge approval
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
