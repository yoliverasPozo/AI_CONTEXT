# Session: GitHub-native agent inbox and event hooks

Date: 2026-10-26

## Coordination

Protocol: AI_CONTEXT coordination v1 (optional)
Task ID: 2026-10-26-agent-inbox-hooks
Status: review
Current owner: ChatGPT implementation/proposal
Next owner: user / independent PR reviewer
Updated: 2026-10-26 (UTC-04:00; precise commit time in Git)
Repository: yoliverasPozo/AI_CONTEXT
Base branch: main
Work branch: feat/agent-inbox-hooks
Last inspected commit: e7ef9c530bb04fd5a15c8f2298a19228dd33a7ae (squash merge of PR #4)
Last tested commit: not run (GitHub CI to be evaluated at latest PR head)
Pull request: draft PR to be opened (not merged)
Continuation of: docs/sessions/2026-10-26-three-agent-roundtrip.md

### Acknowledgment / transfer history

- ChatGPT accepted the user request to merge PR #4 and design an opt-in queue
  and hooks before trialing AI_CONTEXT on another project.
- The previous trial PR #4 was merged to main as `e7ef9c530bb04fd5a15c8f2298a19228dd33a7ae`, with its four CI jobs green.
- Proposed inbox work is separate, on `feat/agent-inbox-hooks`; implementation
  review and event-delivery trial are pending. No auto-agent execution claimed.

## Goal

Make cross-agent handoffs discoverable in GitHub, with automated queue-label
synchronization on opt-in PRs and explicit setup instructions for Work
event-triggered tasks, Codex review, and ChatGPT monitoring.

### Scope and authorization

- Allowed: modify this repository in a separate branch, document the feature,
  add an opt-in GitHub Actions label router, test the change and open a draft PR.
- Not authorized: merge the new feature PR, deploy or configure external
  webhooks/credentials, auto-run agent code, change other repositories.
- Acceptance: default CLI unaffected; labels reflect opted-in PR descriptions
  on relevant events; no auto-execution or escalation of authority; limitations
  and setup steps documented; PR checks pass; later live hook trial planned.

## Investigation

- Verified PR #4 merged; read existing coordination, project context, CLI CI.
- Current OpenAI documentation confirms Work event-triggered tasks on supported
  GitHub PR activity and separate Codex automatic PR reviews or Codex Action.
- GitHub Actions can react to PR event types from the default branch. GitHub
  documents limitations on workflows triggered by GITHUB_TOKEN actions.

## Decisions

- Keep GitHub labels an optional index, not source-of-truth handoff state.
- Route via literal PR-body marker; six managed labels only; no fork PR automation.
- No code checkout in privileged PR event; no third-party outbound webhook.
- No automatic LLM invocation or merge; consumers require individual setup.

## Changes Made

- New `.github/workflows/agent-handoff-inbox.yml` (opt-in event label routing).
- New `docs/AGENT_INBOX.md` (search URLs, role adapters, boundaries).
- ADR 0004 as experimental design and this session handoff.
- Coordination/README/context references updated in same feature PR.

## Tests and Validation

| Check | Evidence | Result |
| --- | --- | --- |
| PR #4 merge and CI | GitHub PR #4 and its pre-merge Actions | passed, unrelated to new feature |
| New inbox workflow | `.github/workflows/agent-handoff-inbox.yml` | pending merge to default branch; cannot yet test event delivery |
| New feature CI | new feature PR head | pending |
| Native Work event-triggered setup | user account/workspace | not configured in this branch |
| Codex automatic reviews | repo settings | not configured in this branch |
| ChatGPT status monitoring | separate event/conditional task | subject to user account task availability |

## Problems Encountered

- Event-driven queue labels do not automatically resume the originating chat.
- Hook delivery and current repository Actions permissions are unverified.
- A real loop/dedup test needs the workflow on default branch, after review.
- No production or private-system data is involved.

## Current Result

Opt-in GitHub inbox prototype proposed for draft PR; no downstream agent
subscription has been installed. The feature must not be called fully
automated until event delivery and account-level integrations are verified.

## Next Steps

1. Review CI and the draft PR; correct issues before separate merge approval.
2. Enable a Work GitHub PR event-triggered task, Codex automatic review, and
   ChatGPT conditional monitoring through their individual supported settings.
3. Trial a single opt-in PR in AI_CONTEXT: transitions `work -> codex ->
   chatgpt -> done`, verify actual events, no duplicate execution, user approval.
4. Only then apply this optional layer to another project.
