# Session: Central Project reconciliation prototype

Date: 2026-11-02

## Coordination

Task ID: 2026-11-02-central-project-sync
Status: review
Current owner: Codex implementer
Next owner: independent reviewer / user
Repository: yoliverasPozo/AI_CONTEXT
Base branch: main
Work branch: feat/central-project-sync-prototype
Last inspected base: 8d3b6707fe292662ca879dd399b3c53aee632030
Last tested revision: working candidate on the recorded base; verify actual PR head after publication

## User Goal

Build a reviewable optional central reconciliation prototype that can inspect
an explicitly allowlisted portfolio and propose missing Project items and
verified handoff projections. Preserve manual values, dependencies, owner
decisions and production holds. Keep actual writes and activation outside this
prototype. The user authorized autonomous implementation and a draft PR.

## Investigation

- Read current repository instructions, context, coordination/inbox rules,
  relevant ADRs and sessions, live PRs, router runs and exact-head review receipts.
- Main's context still described merged PR #5 as a draft. PR #9's permission
  fix is also merged. Genuine router runs now succeed.
- PR #8 remains a synthetic transition: current marker/label says ChatGPT,
  while its exact-head ready journal names Work. No published receiving
  acknowledgment exists. This branch does not modify that trial or invent one.
- Automatic review evidence on PR #7 (`New commits`) and #8 (`PR opened`)
  is distinct from PR #6's manual review. Passing CI is not handoff delivery.
- Current GitHub schema and official docs confirm Project item archive filtering
  uses `archivedStates`, whose default omits archives. Query both states.
- Official OpenAI documentation distinguishes GitHub event tasks, existing-chat
  schedules, Codex review and separately invoked cloud implementation tasks.

## Decisions

- Add a source-only standard-library example; leave the offline initializer
  and its packaged resources unchanged. ADR 0005 remains experimental.
- Choose central periodic reconciliation as the proposed future shape without
  installing a workflow or schedule or claiming measured savings.
- Expose plan-only live/offline modes, with no executable apply path or credential
  provisioning. No GitHub writes, messages, labels, dispatches or scope grants.
- Require archived identities, exact allowlists, complete bounded reads and
  literal configured current-head journal/marker/label agreement.
- Preserve manual actor values and all gates/status/dependencies. Terminal PR
  lifecycle produces a suggestion only. Cursor proposals record observations,
  never delivery, acknowledgment or exactly-once execution.

## Changes Made

- `examples/project_sync/`: pure planner, bounded GraphQL collector using an
  existing `gh` login, plan-only CLI and generic config/snapshot examples.
- `tests/test_project_sync.py`: meaningful offline planner/CLI and GraphQL
  boundary cases, including conflicts, archives, terminal state, pagination,
  stale-head readback, budgets, scope failure and malformed observations.
- `docs/PROJECT_SYNC.md`, ADR 0005 and implementation plan: scope, auth boundary,
  schemas, dry-run commands, limitations, future concurrency/recovery proof.
- `docs/AGENT_INBOX.md`: current invocation distinctions, blob-revision dedup,
  conflict preservation, quiet no-change behavior and optional adapter pointer.
- `docs/AI_CONTEXT.md`, README and this journal: synchronized public state and
  continuation pointers. Historical journals remain unchanged.

## Tests

- Baseline: 18/18 existing tests passed with this checkout's `src` import
  provenance explicitly asserted using process-local `PYTHONPATH`.
- New planner/CLI/collector tests were added before implementation and initially
  failed because their modules were absent. Additional malformed-marker,
  metadata and missing-field tests failed against the first implementation;
  the validation was tightened and those tests passed.
- Candidate targeted suite: 31/31 new tests passed; complete suite 49/49 passed
  with checkout import provenance. Whitespace and local Markdown targets were
  also checked. Actual publication head and its remote CI must still be checked
  before accepting the PR.
- Generic CLI simulation: 2 additions, 1 verified blank actor proposal,
  1 terminal suggestion preserving blocked status/gate, 1 unknown diagnostic,
  and 1 notification/cursor proposal. No files or services changed.
- One live prototype attempt using existing authentication exited 2 with
  `existing gh login lacks read:project access; no scopes were changed`.
  No partial plan was emitted, no credentials were printed, and no access
  expansion or retry with different credentials was attempted.

## Problems Encountered

- Existing authentication lacks Project read access. Complete live collector
  operation therefore remains unverified; controlled GraphQL fixtures and schema
  inspection are not a replacement for that acceptance evidence.
- Nested fields/labels exceeding 100 entries deliberately stop collection.
  Missing/redacted identities and changed pagination totals also stop rather
  than silently proposing duplicates.
- A controller snapshot is not atomic. Concurrent head/item changes and
  exactly-once notification delivery are outside this plan-only prototype.
- Independent review reproduced two important proposal-boundary bugs: a fenced
  whole-journal example could be treated as live metadata, and a configured
  actor field could target an approval/status field. Failing regressions were
  added; section selection is now fence-aware across the whole document and
  the sole projection field is exactly `Next actor`. Tests also preserve normal
  journals with unrelated fenced examples. Authentication guidance was qualified
  for organization versus personal Projects.

## Current Result

A tested optional proposal engine and its public-safe documentation are ready
for independent review. No apply capability, new credentials, workflow,
schedule, notification delivery or agent execution was activated. Live-read
acceptance and any future operational rollout remain separate decisions.

## Next Steps

1. Independent reviewer: inspect the exact candidate/PR head, full tests,
   privacy boundary and conservative identity/admission behavior.
2. User/owner: choose authentication separately if actual live collection is
   wanted; first verify complete reads and measured budgets without writes.
3. Before any future apply implementation, prove field provenance, manual
   override preservation, current-state checks, duplicate/restart recovery and
   reversal of controller-owned changes. Resolve the existing trial's owner
   conflict independently.
