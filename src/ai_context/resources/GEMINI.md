# Shared Project Context

This repository uses a vendor-neutral project memory layer under `docs/`.

Before substantial work:

1. Read `docs/AI_CONTEXT.md`.
2. Read relevant accepted records in `docs/decisions/`.
3. Read relevant recent handoffs in `docs/sessions/` when prior experiments, debugging, or unfinished work matter.
4. Inspect the actual code, configuration, tests, and Git state before relying on documentation alone.

When sources conflict, current observable repository/runtime truth and accepted decision records take precedence over stale summaries or remembered chat context.

After substantial work, update the shared memory when appropriate:

- refresh `docs/AI_CONTEXT.md` when the current state changes;
- add a session handoff when another agent or developer would benefit from the continuation context;
- create an ADR for an important durable decision;
- preserve meaningful failed approaches that should not be rediscovered.

If prior conversation context is missing, compacted, or ambiguous, reconstruct the project from these files and the repository rather than guessing.

Do not store secrets, tokens, credentials, sensitive personal information, full transcripts, or hidden chain-of-thought in shared context. Store concise engineering conclusions, requirements, tradeoffs, test results, and decisions.
