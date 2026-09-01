# Project Agent Instructions

This repository uses a shared, repository-native AI context layer.

## Before Substantial Work

Read:

1. `docs/AI_CONTEXT.md`
2. Relevant accepted decisions under `docs/decisions/`
3. Relevant recent handoffs under `docs/sessions/` when prior debugging, experiments, or unfinished work may matter

Then inspect the current code, configuration, tests, Git state, and runtime evidence before trusting documentation blindly.

## Source-of-Truth Order

When sources disagree, prefer:

1. Current code, configuration, tests, and observable runtime behavior
2. Accepted decision records
3. `docs/AI_CONTEXT.md`
4. Relevant recent session journals
5. Remembered or summarized conversation context

## After Substantial Work

- Update `docs/AI_CONTEXT.md` if the current project state changed.
- Create or update a session handoff when future continuation would benefit from it.
- Create an ADR for important architectural or design decisions.
- Preserve meaningful failed approaches that future agents might otherwise repeat.
- Keep context concise; do not turn `AI_CONTEXT.md` into a chronological log.
- Commit context updates alongside the code they describe whenever practical.

## Context Recovery

If conversation history appears incomplete, compacted, interrupted, or inconsistent with the workspace, reconstruct the task from the repository before continuing. Read the shared context, relevant decisions and handoffs, inspect Git state and source files, and determine what has already been completed and what remains unresolved.

## Safety and Privacy

Do not store secrets, credentials, private keys, tokens, sensitive personal information, full raw chat transcripts, or hidden chain-of-thought in shared project context.

Record concise engineering conclusions, constraints, tradeoffs, tests, failures, and decisions instead.
