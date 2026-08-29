# AI_Context Convention

This document defines the minimal AI_Context convention independently of any specific AI product.

It is intentionally lightweight. Implementations may extend it.

## Required concept: current project context

An AI_Context-enabled project SHOULD maintain a human-readable current-state document.

Recommended path:

```text
docs/AI_CONTEXT.md
```

The document SHOULD summarize, where applicable:

- project goal;
- current architecture;
- current working state;
- known problems or unfinished work;
- important recent changes;
- important decisions;
- active work;
- likely next steps;
- important files or locations;
- relevant recent verification.

The current-state document SHOULD be curated rather than append-only.

## Recommended concept: decision records

Projects SHOULD preserve durable architectural or design decisions separately from the current-state summary.

Recommended directory:

```text
docs/decisions/
```

A decision record SHOULD identify:

- context/problem;
- decision;
- alternatives considered;
- rationale;
- consequences;
- status.

A superseded decision SHOULD normally remain in history with its status changed or a link to its replacement rather than being silently erased.

## Recommended concept: session handoffs

Projects MAY maintain session handoffs for substantial work.

Recommended directory:

```text
docs/sessions/
```

A session handoff SHOULD capture only information likely to help later continuation, such as:

- goal;
- investigation/discoveries;
- decisions;
- changes;
- validation;
- meaningful failed approaches;
- unresolved problems;
- resulting state;
- next steps.

Projects SHOULD NOT create session records for every trivial edit.

## Agent entry points

Each AI tool MAY use its own native repository instruction file.

That file SHOULD act as an adapter into the shared context rather than becoming a separate competing memory store.

An adapter SHOULD tell the agent:

1. where shared context lives;
2. when to read it;
3. when to update it;
4. how to recover after missing or compressed conversation context;
5. what information must not be stored there.

## Source-of-truth behavior

AI_Context documentation MUST NOT be treated as infallible.

Agents SHOULD verify material claims against current code, configuration, tests, Git state, and observable runtime behavior when available.

Projects SHOULD define an authority order for conflicts. A recommended default is:

1. current code/configuration/tests/runtime evidence;
2. accepted decision records;
3. current project context;
4. recent session handoffs;
5. conversation memory.

When documentation and reality diverge, the discrepancy SHOULD be corrected.

## Maintenance behavior

After substantial work, an AI agent or developer SHOULD:

- update current context if the current state changed;
- create/update a session handoff if continuation context is valuable;
- create a decision record if a durable decision was made;
- remove or rewrite stale current-state information;
- keep historical detail out of the current-state briefing when it can be linked instead.

Context changes SHOULD be committed with the work they describe when practical.

## Privacy and security

Shared context MUST NOT be used as a secret store.

Projects SHOULD NOT intentionally place the following in shared AI_Context files:

- credentials;
- private keys;
- API tokens;
- passwords;
- sensitive personal information unrelated to the project;
- private customer data inappropriate for source control;
- raw hidden model chain-of-thought;
- full conversation transcripts by default.

Useful engineering conclusions and concise rationale SHOULD be recorded instead of hidden reasoning traces.

## Portability

The canonical shared-memory layer SHOULD use formats that are readable without a specific AI vendor or proprietary tool.

Plain Markdown in Git is the reference implementation.

Machine-readable metadata MAY be added, but SHOULD NOT make the human-readable layer unusable.

## Bounded context

Projects SHOULD optimize shared context for signal rather than volume.

The current-state document SHOULD remain small enough to serve as a practical briefing. Historical detail SHOULD move into linked decision and session records.

## Interoperability goal

A project follows the spirit of AI_Context when a capable new developer or AI agent, without access to previous private chats, can inspect the repository and reconstruct enough of the project's goals, current state, important decisions, unresolved work, and next steps to continue responsibly.
