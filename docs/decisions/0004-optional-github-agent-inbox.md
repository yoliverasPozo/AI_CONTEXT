# Decision: Trial an optional GitHub-native agent inbox

Date: 2026-10-26
Status: Experimental (proposal; not yet accepted)

## Context

AI_CONTEXT coordination v1 preserves durable handoffs, but in the three-agent
trial a human had to relay a PR pointer for each receiving session. We need
discoverable queue items and eventual event-triggered consumers while keeping
authorization, concurrency, evidence and approval boundaries explicit.

## Decision

Propose a **separate optional layer** built from GitHub PRs and six `ai-next:*`
labels. A single exact PR-body marker `<!-- ai-context-next: work -->`
(with other permitted role values) describes the next *notification target*.
A default-branch `pull_request_target` GitHub Action reconciles only these
labels on same-repository PRs and marks merged or closed PRs accordingly.

The session journal remains authoritative for authorization, ownership,
acknowledgment and evidence. Labels are advisory indexes, not locks. The router
must not check out or run untrusted PR code, invoke an LLM, inspect secrets,
auto-merge, or execute a delegated task. Downstream Work event-triggered tasks,
Codex automatic review/Actions, or ChatGPT conditional monitoring are
**separate opt-in configurations**. This repo makes no claim to configure them.

## Alternatives Considered

- Separate database or event bus: deferred; GitHub labels and PR events are
  enough for discoverability without an always-on hosted service.
- Auto-execute Codex on every labeled PR: rejected initially due to key,
  sandbox, prompt-injection and authorization risks.
- Automatically wake an existing Chat conversation: not a supported contract.
- Put a queue database in `docs/AI_CONTEXT.md`: rejected as redundant state
  and unnecessary merge contention.

## Consequences

- Workflows are functional only after merging to the default branch and
  enabling repository Actions permissions; this feature branch is a proposal.
- Labels can be stale until the next relevant PR event; agents must always
  verify live PR state and the referenced journal before execution.
- An external event subscription may observe PR activity, but notification
  does not prove another agent executed or acknowledged a handoff.
- Real end-to-end event delivery, deduplication/no-loop behavior and
  permissions require a controlled trial before changing this ADR's status.
- Nothing about this proposal changes experimental ADR 0003, existing default
  CLI output, or support for non-GitHub projects.

## Supersedes / Superseded By

None. Optional extension to coordination v1.
