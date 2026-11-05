# Review completion gate investigation

Status: proposal only. No workflow, branch protection, ruleset, App permission,
review request, scheduler or routing setting was added or changed.

## Observed merge race

Public [PR13](https://github.com/yoliverasPozo/AI_CONTEXT/pull/13) reviewed head:
`4d4a7935fac183d891a423c44a18c68a5b546b9e`.

| Evidence | UTC on November 4, 2026 |
| --- | --- |
| PR Lens check completed, success | 18:57:25 |
| PR13 merged | 18:58:09 |
| Codex submitted COMMENTED review | 18:58:10 |
| Codex P2 inline finding created | 18:58:11 |
| Codex summary says code review completed | 18:58:13.351031 |
| PR Lens sticky comment last updated | 19:02:42 |

Codex finished after merge. PR Lens's later comment update does not establish
when its findings first appeared. Its successful check establishes completion of
that check, not absence or resolution of findings. The current sticky comment
lists two findings. Codex's current-head summary says completed, with unresolved
findings; completion alone would still be insufficient for merge readiness.

Read-only REST inspection found `main` unprotected (branch-protection endpoint
404, "Branch not protected") and no repository rulesets (`[]`). Nine check runs
were returned for this head: four test jobs, four router runs and PR Lens. No
Codex check run was exposed. These are observations at inspection time, not a
guarantee about future integration behavior.

## Recommended gate

Use a required current-head status check, provisionally `AI review complete`,
plus all four existing CI jobs, PR Lens from its expected GitHub App, and resolved
review conversations. Block direct pushes and avoid bypass actors for the
ordinary merge path. Keep merge authorization separate from passing these gates.
Do not enable auto-merge as part of this change.

The additional check needs a trusted evaluator; it does not exist in this PR.
GitHub required approvals alone cannot attest that both observed integrations
finished: Codex submitted COMMENTED, while PR Lens publishes a check and sticky
comment. Requiring one or two approvals is not a substitute for these signals.

Proposed evaluator contract:

1. Fetch the current PR head and paginate all relevant checks, reviews, comments
   and review threads. Missing, truncated, ambiguous, malformed or stale evidence
   blocks. Never execute PR code or interpret comment text as commands.
2. Require Codex's authenticated bot-authored completion evidence for the exact
   full head SHA, with code review completed. Observed bot account ID is
   `199175422`; pin identity, not a copied marker or arbitrary user's reaction.
   The observed versioned summary marker is undocumented integration metadata;
   an adapter requires explicit fixtures and validation before deployment.
   A thumbs-up or the existence of any older review is insufficient.
3. Require the exact-head PR Lens check to be completed/success from App
   `4690539` (`coldtea-pr-lens`), and matching bot-authored review state/comment
   for that full SHA. Observed bot account ID is `320153949`. Treat later edits
   as invalidating prior assessment; neither the drawing marker nor a successful
   check alone proves findings have been handled.
4. Require finding disposition as well as completion. Codex's
   `has_unresolved_findings: true`, open review threads or undisposed PR Lens
   findings block. Since PR Lens findings can live only in a sticky comment,
   GitHub's resolved-conversation rule does not cover all of them. A trusted
   reviewer must bind each accepted/fixed/declined finding disposition to the
   exact current head. A clean re-review can replace that evidence; do not infer
   resolution from disappearance, a human resolving a thread, or CI success.
5. Re-fetch the head before publishing the result on that exact commit. A push
   requires fresh completion/disposition; no old-head success carries forward.
   Include source identities, full head SHA, evidence IDs and decision reasons.

An eventual event-driven implementation should invalidate/re-evaluate on pushes,
review submissions/dismissals, relevant comment edits/deletions and check
completion. Test same-head re-reviews, stale success, edited findings, forks,
pagination, bot identity spoofing, API failure and race handling. Verify event
delivery and workflow/check SHA association in a sandbox: no assumption that
every review event runs against the PR head. No recurring polling is required.

## Alternatives and activation boundaries

- Manual interim rule: keep the corrective PR draft. Before marking ready and
  before any separately authorized merge, inspect both reviewers at the exact
  final head, resolve/dispose findings, verify CI, and recheck the head. This is
  a human procedure, not enforced GitHub protection.
- Native rules alone: require CI and PR Lens's App-pinned check, stale approval
  dismissal and conversation resolution. Useful baseline protection but does
  not provide the missing Codex completion or sticky-comment disposition gate.
- Trusted App/evaluator plus ruleset: recommended enforcement, with additional
  implementation and event-race acceptance needed before activation.

Activation needs separate owner approval for the exact required contexts/App
sources, stale-review and bypass policy, trusted evaluator and minimal permissions.
First create/validate the check on an isolated PR; then enable the required rule
and prove missing/in-progress/stale reviewers block merge without performing a
merge. Do not require a nonexistent check on main and strand all PRs. Do not
grant broader credentials or install a new App without explicit authority.

GitHub documents App-pinned required checks and latest-SHA requirements in
[ruleset rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
and [required-check troubleshooting](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).

## PR13 findings disposition

- Codex P2 terminal omission: reproduced on merged main for both active and
  archived originals. Corrected by a terminal original-ID subset check before
  typed count-change restart; regression also verifies durable failure evidence
  and that a spent operation cannot be promoted by another apply.
- PR Lens count-guard ordering: retain fail-closed ordering. Moving the restart
  ahead of item/cursor/count/preservation checks would weaken safety. Valid
  count-only changes can restart; overflow or incomplete terminal pages stop.
- PR Lens repeated field-ID set: confirmed redundant per item. Compute it once
  per page, preserving all metadata checks and field validation.
