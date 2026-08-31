# AI_CONTEXT Project Agent Instructions

This repository both **defines** the AI_CONTEXT convention and **uses it on itself**.

The reusable templates under `templates/` and examples under `examples/` are generic reference material. The files under `docs/AI_CONTEXT.md`, `docs/decisions/`, and `docs/sessions/` are this repository's own live shared project memory.

## Before Substantial Work

Read:

1. `docs/AI_CONTEXT.md`
2. Relevant accepted decisions under `docs/decisions/`
3. Relevant recent handoffs under `docs/sessions/` when prior debugging, experiments, or unfinished work may matter

Then inspect the current repository, Git state, documentation, examples, templates, and any automated checks before trusting shared context blindly.

## Source-of-Truth Order

When sources disagree, prefer:

1. Current repository contents and observable behavior
2. Accepted decision records
3. `docs/AI_CONTEXT.md`
4. Relevant recent session journals
5. Remembered or summarized conversation context

## Project-Specific Rules

- Keep AI_CONTEXT vendor-neutral. Do not make the convention depend on one model, agent, IDE, API, or company.
- Keep the shared memory format human-readable and Git-native unless an accepted decision explicitly extends it.
- Preserve the distinction between **generic reference files** (`templates/`, `examples/`) and this repository's **live project memory** (`docs/AI_CONTEXT.md`, `docs/decisions/`, `docs/sessions/`).
- When changing the convention itself, check whether `README.md`, `docs/CONVENTION.md`, `docs/ADOPTION.md`, templates, examples, and live context need coordinated updates.
- Do not silently turn optional guidance into a required part of the convention. Record substantial compatibility or format decisions in an ADR.
- Keep the core pattern lightweight. New tooling should support the Markdown convention rather than make the convention dependent on the tooling.

## After Substantial Work

- Update `docs/AI_CONTEXT.md` if the current project state changed.
- Create or update a session handoff when future continuation would benefit from it.
- Create an ADR for important architectural, compatibility, naming, or format decisions.
- Preserve meaningful failed approaches that future agents might otherwise repeat.
- Keep `docs/AI_CONTEXT.md` concise and current rather than chronological.
- Commit context updates alongside the changes they describe whenever practical.

## Context Recovery

If conversation history appears incomplete, compacted, interrupted, or inconsistent with the repository, reconstruct the task from the repository before continuing. Read the shared context, relevant decisions and handoffs, inspect the current files and Git state, and determine what has already been completed and what remains unresolved.

## Safety and Privacy

Do not store secrets, credentials, private keys, tokens, sensitive personal information, full raw chat transcripts, or hidden chain-of-thought in shared project context.

Record concise engineering conclusions, requirements, constraints, tradeoffs, tests, failures, and decisions instead.
