# Shared Project Context

This repository maintains tool-neutral project memory under `docs/` so work can continue across Claude Code, other AI agents, and human developers.

Before substantial work, read:

- `docs/AI_CONTEXT.md`
- relevant accepted records in `docs/decisions/`
- relevant recent files in `docs/sessions/` when prior investigation or unfinished work matters

Then verify the current repository state directly. Code, tests, configuration, Git state, and observable runtime behavior take precedence over stale notes.

After substantial work:

- update `docs/AI_CONTEXT.md` when current state changes;
- add a session handoff when future continuation would benefit;
- add an ADR for durable architectural decisions;
- record important failed approaches so they are not repeated;
- keep the current-state file concise rather than chronological.

If conversation context is missing or compressed, recover from the repository instead of guessing or repeating completed work.

Do not place secrets, credentials, sensitive personal data, raw chat transcripts, or hidden chain-of-thought in shared context. Preserve concise engineering conclusions, requirements, tradeoffs, validation results, failures, and decisions.
