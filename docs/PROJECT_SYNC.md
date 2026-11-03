# Optional central Project reconciliation prototype

The planner invoked with `python -m examples.project_sync` prints a reviewable JSON proposal for
one explicitly selected GitHub Project. It can inspect real GitHub data through
an existing `gh` login or simulate the same planner using a local snapshot.
**It cannot write to GitHub, apply a plan, send notifications, save a cursor,
create credentials, run an agent, or schedule itself.**

A separate [disabled add-only writer](PROJECT_WRITER.md) has its own explicit
scope, state digest, approval and execution gates. The planner never invokes it.

This is an experimental adapter to [coordination v1](COORDINATION.md) and the
[handoff inbox](AGENT_INBOX.md), not a new requirement of AI_CONTEXT. The core
initializer and its offline, dependency-free behavior are unchanged. See
[ADR 0005](decisions/0005-central-project-projection.md).

## Try the offline simulation

From a source checkout with Python 3.10 or later:

```console
python -m examples.project_sync --config examples/project_sync/config.example.json --snapshot examples/project_sync/snapshot.example.json
python -m unittest discover -s tests -v
```

The generic fixture proposes adding one missing open PR and one explicitly
selected issue, filling one verified blank actor field, and reporting a merged
tracked PR while preserving its blocked status and approval gate. It also
recognizes an archived identity and an unverified handoff. No file or service
is changed. Output is marked `offline-simulation`; it is not live evidence.

The example is source-only, outside the installed `ai-context` command. Keep
real configurations, snapshots and reports in an appropriate private location
outside this public repository. Output can contain private repository names
and current Project values when those are present in the input.

## Explicit configuration

Copy the [generic config](../examples/project_sync/config.example.json) to that
private location and select:

- `project.owner`, `owner_type` (`user` or `organization`), and `number`.
- An explicit `repositories` allowlist of exact `owner/repository` names.
  Repository names are matched exactly; aliases/case changes need a reviewed
  configuration update rather than inferred scope expansion.
- Explicit relevant issue numbers per repository. All open PRs in each listed
  repository are considered; untracked historical closed PRs are not imported.
- Optional `handoffs`: PR-number strings mapped to exact
  `docs/sessions/*.md` paths. This prevents discovering/executing arbitrary
  paths from PR text. Missing configuration produces unknown handoff state.
- `actor_field` must be exactly `Next actor`. Other fields, including Status,
  approval gates, handoff state and workstream, cannot be projection targets.
  Select exact role-to-journal-owner/Project-value mappings. This prototype
  proposes values; it does not create or validate
  Project select options for a future write.
- Bounded `limits`. Defaults: 100 GraphQL calls, 100 pages per connection,
  50 records per page, remaining rate floor 100, handoff size 65,536 bytes.
  Hard caps are 500 calls, 1,000 pages, 100 records per page and 262,144
  handoff bytes. Each requested repository/issue/handoff consumes this common
  budget. A partial read never produces a partial plan.

No API token belongs in this JSON. There is no credential setup option.

## Live reads and authentication

```console
python -m examples.project_sync --config /private/path/project-config.json --live
```

Live mode invokes only hardcoded GraphQL queries using the existing GitHub CLI
login against `github.com`. It uses JSON variables over standard input, never
shell evaluation or PR-provided executable text. The subprocess has a timeout;
errors are reported without printing its raw output. No authentication refresh,
scope grant, login, token creation or secret inspection occurs.

The existing login needs access to the selected repositories and Project.
GitHub documents `read:project` for queries and `project` for queries/mutations;
an appropriately configured GitHub App installation is a documented path for
organization-owned Projects. For personal user-owned Projects, the documented
route is a classic PAT with `read:project` for reads plus `repo` when private
repository content requires it; a future writer would need `project`. Fine-grained
PAT support and a personal-Project App installation path are not established
by the cited Projects documentation. The prototype does not choose or provision
credentials. If
current credentials lack access, it exits nonzero with a sanitized diagnostic.
Resolve access through a separately authorized credential decision; do not
automatically widen existing credentials. [GitHub Project authentication](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects).

The live collector reads:

1. All Project item identities, including archived items, across complete
   paginated results. The current GraphQL argument is
   `archivedStates: [ARCHIVED, NOT_ARCHIVED]`; the default omits archives.
2. All open PRs in each allowlisted repository across complete pages.
3. Current lifecycle for tracked allowlisted PRs absent from the open list,
   including closed, merged and archived PRs.
4. Only configured relevant issue numbers.
5. Configured handoff blobs at exact PR head revisions, followed by a fresh
   PR read of head, state, marker and labels before admission.

Fields and labels are nested connections bounded at 100 entries. If one is
truncated, collection stops instead of guessing. Collection totals, null nodes,
repeated cursors, duplicate identities, changed page totals, GraphQL errors,
missing rate evidence, budget exhaustion and rate-floor breaches also stop
planning. Missing/redacted Project content is a failure because deduplication
cannot be proven. Unsupported actor field types are rejected. Readable
single-select/text/number/date/iteration values are preserved in terminal
suggestions; other types are not projected or written. [GraphQL Projects schema](https://docs.github.com/en/graphql/reference/projects).

The collector is not an atomic GitHub snapshot. A PR or item can move after a
read. Plans are evidence for review only and must be recollected before any
future write implementation; no claim of concurrent exactly-once behavior is
made.

## Planner rules

Identity is the GitHub content node ID, checked against content kind, repository
and number. Existing archived items count as existing. Duplicate Project item
IDs, content IDs or logical identities refuse the whole proposal. Replaying a
snapshot with all proposed additions represented as items produces no additions.
Nothing is removed, unarchived, reordered or automatically imported from other
repositories. Only open explicitly selected issues are proposed for addition;
historical issue discovery is intentionally absent.

Only a blank actor field can receive a field proposal. A nonblank manual value
is preserved. The planner never infers an actor from an assignee. It never
changes Status, approval gates, dependency edges, views or production holds.
For a tracked closed/merged PR it reports lifecycle separately with
`status_write: false`; merging a PR is not proof that an owner gate is cleared.

A blank actor requires all of:

- One recognized PR-body marker and its sole matching `ai-next:*` label.
- One explicitly configured handoff at the same observed current head, with
  a concrete Git blob revision and complete content.
- One literal `## Coordination` section containing unique `Task ID`, `Status`,
  `Next owner`, and `Repository` lines. Status must be exactly `ready` and
  owner/repository must match the configuration/current PR.
- A nonarchived open PR.

The parser accepts a narrow Markdown subset, selects Coordination headings
outside whole-document Markdown fences, rejects conflicting/malformed metadata
and fences inside that section, and never evaluates document content. A fenced
example elsewhere in the journal is ignored. Missing,
active, blocked, review, complete, cancelled, stale or conflicting state yields
an explicit unknown/conflict diagnostic. It can still propose a missing item;
that addition grants no permission or ownership. Journal status remains curated
source evidence, not a distributed lock or a parsed authorization grant.

Offline snapshots use the normalized schema shown in the
[fixture](../examples/project_sync/snapshot.example.json): `schema_version: 1`,
`complete: true`, project identity/items, `pull_requests`, `issues`, and
`handoffs`. Completeness and handoff observations in a user-supplied snapshot
are asserted input, not independently authenticated GitHub evidence. An exported
UI CSV alone lacks node identities, archived coverage and exact-head blobs;
it must not be relabeled as a complete live snapshot.

## Notification and cursor proposals

An admitted ready handoff yields a notification proposal keyed by:

```text
repository / PR number / head SHA / intended owner / handoff blob SHA
```

`proposed_cursor.observed_keys` records proposed observations, not delivery or
acknowledgment. A reviewed cursor may be provided with `--cursor` on a later
run to suppress an identical proposal. The program never persists it or sends
anything. A new handoff blob revision produces a new key. Existing durable
task/transfer/acknowledgment history still needs human or receiver validation
before any substantive work; this planner does not execute tasks.

Keep observed, notified, acknowledged, started and completed states distinct.
Do not call a review receipt or notification an acknowledgment. Future delivery
requires private durable storage, a single active sender or an atomic claim,
bounded retries and recovery tests. Do not advance a delivered cursor merely
because a proposal printed. Polls with no actionable change should be quiet.

## Central reconciliation and future activation

A single periodic reconciliation is the proposed first deployment shape. It
avoids adding a workflow to every repository and supports repository allowlists
beyond native auto-add rule limits. It does deterministic reads/planning rather
than invoking an agent per repository. This is a design choice, not a measured
cost or reliability result. Event subscriptions can remain delivery adapters;
neither labels nor Project fields authorize work.

No workflow, schedule, deployment, token or apply mode ships in this prototype.
An eventual implementation must separately establish:

1. Suitable explicitly approved authentication, actual complete live reads and
   visibility into archived identities, with measured API/runtime budgets.
2. Current field IDs/options and per-field provenance, preserving any manual
   changes or conflicts rather than overwriting them.
3. Revalidation of head, journal revision and item values before each write;
   expected-value checks, concurrency behavior and restart recovery.
4. Idempotent add/fill operations, bounded retries, recovery evidence, a reviewed
   before/after receipt and a method to reverse only controller-owned changes.
5. Independent tests of genuine event receipt, duplicate delivery and published
   receiver acknowledgment. Owner decisions, dependencies and production holds
   remain separate gates.

Until those conditions are proven, apply remains deferred. Unknown observations
and access failures stay visible; a simulation or green test suite cannot stand
in for live acceptance.
