# Session: GitHub inbox Work event-delivery smoke test

Date: 2026-10-27

## Coordination

Protocol: AI_CONTEXT coordination v1 / experimental inbox ADR 0004
Task ID: 2026-10-27-inbox-work-event-smoke
Status: ready
Current owner: ChatGPT coordinator (outgoing until Work acknowledgment)
Next owner: ChatGPT Work
Updated: 2026-10-27 (America/Puerto_Rico; exact time in Git history)
Repository: yoliverasPozo/AI_CONTEXT
Base branch: main
Work branch: trial/inbox-work-event-2026-10-27
Last inspected commit: verify current GitHub PR head; journal initially staged before the PR exists
Last tested commit: not run; documentation-only event smoke test
Pull request: see the PR containing this session (initially not assigned)
Continuation of: docs/sessions/2026-10-26-agent-inbox-hooks.md

### Acknowledgment / transfer history

- ChatGPT coordinator published this public-safe trial request for the existing **Work Handoff Watcher**, monitor-and-report mode. Receiving Work acknowledgment or notification is **not yet confirmed**.
- Work may report what it actually received and verified; do not claim receipt merely because the PR label appears.

## Goal

Verify that GitHub's opt-in PR-body marker is routed to `ai-next:work`
and that the separately configured Work event-triggered Handoff Watcher can
receive and report the event without the human relaying a PR number.

### Scope and authorization

- Work's allowed action: **read/monitor/report only**. Inspect the current PR,
  the `ai-next:work` label, actual branch SHA, this session, and CI if present.
  Send one user-facing event notification with PR link, exact SHA, and observed
  handoff state. Do not modify files, comments, labels, tasks, or PR metadata.
- The user has authorized this harmless event-delivery experiment only.
  No merge, deployment, PR ownership takeover, or code execution is authorized.
- Acceptance: real GitHub label assignment confirmed; actual Work event delivery
  separately confirmed by an event-triggered run/report; no duplicate action or
  unexpected mutation. GitHub labeling alone is **not** a Work receipt.

## Investigation

- The inbox router is installed on the default branch as
  `.github/workflows/agent-handoff-inbox.yml`.
- `docs/AGENT_INBOX.md` defines `<!-- ai-context-next: work -->` and
  `ai-next:work` for explicitly opted-in handoffs.
- A prior controlled ChatGPT → Work → Codex → ChatGPT round-trip succeeded
  using manual transfers. Native event delivery has not yet been demonstrated.

## Decisions

- Test Work notification before attempting automatic repository modifications.
- Keep the scope in this session authoritative; the PR marker is only an index.
- Do not treat Codex's automatic review of this PR, if it occurs, as a Work
  receipt or a completion of this handoff.

## Changes Made

- ChatGPT: created this trial session on a new branch.
- Work: not run or not yet observed.

## Tests and Validation

| Check | Revision/evidence | Result |
| --- | --- | --- |
| GitHub PR open and label `ai-next:work` | Inspect PR issue labels | Pending |
| GitHub handoff Action | PR event on default-branch Action | Pending |
| Native Work Handoff Watcher event | Work task run/report | Not confirmed |
| Current CI | Head commit of this PR | Pending |
| ChatGPT notification/acknowledgment | Separate check after Work event | Not started |

## Problems Encountered

- GitHub Actions writes using the default `GITHUB_TOKEN` may not retrigger
  another GitHub Action. A user/API-authored PR description edit after labeling
  can generate a separate supported PR event for testing Work delivery.
- Work may monitor/report without publishing an acknowledgment in Git.
  That does **not** satisfy a repository-write handoff test.
- Read-only monitoring cannot prove general autonomous implementation.

## Current Result

Awaiting actual GitHub routing and Work event delivery; the trial is not complete.

## Next Steps

1. GitHub: open a PR carrying this journal and exactly one Work routing marker.
   Confirm the router adds `ai-next:work` without mutating unrelated labels.
2. Work Handoff Watcher: receive a supported PR event, verify this current
   journal and head revision, notify the user **once**, and do nothing else.
3. ChatGPT: verify any actual Work report; only after observed delivery,
   consider a separate `ai-next:chatgpt` routing check. Do not fake a
   Work-to-ChatGPT handoff or merge the test PR.
