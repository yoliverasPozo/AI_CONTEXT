# Decision: Dogfood AI_CONTEXT in the AI_CONTEXT repository

Date: 2026-08-31
Status: Accepted

## Context

AI_CONTEXT exists to preserve project state, decisions, and useful development history in the repository so humans and different AI agents can recover context without relying on one conversation.

If the reference repository only publishes templates but does not use them itself, important weaknesses in the convention may remain theoretical. The repository also needs durable continuity for its own future additions, including possible CLI tooling, validation, CI integrations, and compatibility work.

At the same time, using AI_CONTEXT on itself creates a potential source of confusion: the generic templates that teach adopters how to use the convention must remain distinct from the live files describing this repository's own state.

## Decision

The AI_CONTEXT repository will use AI_CONTEXT on itself.

It will maintain a live project-memory layer consisting of:

- `docs/AI_CONTEXT.md` for current project state;
- `docs/decisions/` for durable project decisions;
- `docs/sessions/` for substantial development handoffs; and
- root-level agent instruction adapters as needed, beginning with `AGENTS.md`.

The existing `templates/` and `examples/` directories remain generic reference material for adopters and must not be repurposed as this repository's live memory.

Changes to the AI_CONTEXT convention should be evaluated against this live implementation. Friction discovered while dogfooding the convention is valid input for improving the convention, templates, and future optional tooling.

## Alternatives Considered

### Keep the repository as reference material only

This would make the repository simpler, but future work on AI_CONTEXT would rely on ordinary chat/project memory and would fail to demonstrate the pattern under real use.

### Store the repository's live state inside `templates/`

Rejected because templates should remain clean, reusable examples. Mixing real project state into them would make copying and understanding the convention harder.

### Create a separate repository solely to demonstrate AI_CONTEXT

This could provide a clean example, but would not test whether the convention can maintain the project that defines it. A separate example repository may still be useful later.

## Rationale

Dogfooding provides continuous practical validation of the convention while also solving the repository's own continuity problem.

Keeping the live memory under `docs/` and generic material under `templates/` and `examples/` preserves a clear boundary between **the specification/reference** and **an actual instance of the pattern**.

This also creates a concrete example that visitors can inspect rather than requiring them to infer the workflow from documentation alone.

## Consequences

Benefits:

- AI_CONTEXT becomes a real example of its own convention.
- Future AI agents can recover the project's actual state from the repository.
- New features can be evaluated against real context-maintenance needs.
- Visitors can compare generic templates with a populated implementation.

Costs and risks:

- Contributors must keep live context reasonably current.
- Documentation can become self-referential, so naming and directory boundaries must stay clear.
- Context maintenance must remain lightweight enough that dogfooding does not become documentation overhead.

Follow-up work:

- Reference the live implementation from the README.
- Use the live context during future feature development.
- Revise the convention if repeated real-world friction demonstrates that the current format is insufficient.

## Supersedes / Superseded By

None.

---

Create an ADR only when a decision is important enough that a future developer or AI agent might otherwise revisit, reverse, or misunderstand it.
