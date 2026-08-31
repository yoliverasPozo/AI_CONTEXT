# Project Context

## Project Goal

AI_CONTEXT defines and demonstrates a lightweight, vendor-neutral, repository-native shared-memory pattern for AI-assisted software projects.

The project aims to let humans and different AI coding agents preserve and recover the useful engineering state of a project without depending on any single chat history or model context window.

The repository should serve both as:

1. a clear explanation and reusable reference implementation of the convention; and
2. a real project that uses AI_CONTEXT on itself so future development demonstrates the workflow in practice.

## Current Architecture

The repository is organized into two layers:

### Reference layer

- `README.md` — public introduction, rationale, workflow, and high-level documentation.
- `docs/CONVENTION.md` — lightweight normative description of the AI_CONTEXT convention.
- `docs/ADOPTION.md` — guidance for introducing AI_CONTEXT into an existing project.
- `templates/` — generic templates for current-state context, ADRs, and session handoffs.
- `examples/` — generic agent-specific adapters and bootstrap examples.
- `assets/` — repository artwork and presentation assets.

### Live project-memory layer

- `AGENTS.md` — repository-specific instructions directing compatible agents into the shared context layer.
- `docs/AI_CONTEXT.md` — this repository's current project state.
- `docs/decisions/` — durable decisions about the AI_CONTEXT project itself.
- `docs/sessions/` — useful handoffs from substantial development sessions on AI_CONTEXT.

The reference templates remain generic. The live project-memory files contain AI_CONTEXT's own real state and history.

Because the live memory is stored in Git, its evolution is also versioned: commits preserve historical project state, diffs expose context changes for review, and incorrect memory can be reverted alongside code or documentation.

## Current State

The project is public under the MIT License and currently provides:

- the AI_CONTEXT concept and rationale;
- a repository-native Markdown convention;
- a current-state context template;
- an ADR template;
- a substantial-session handoff template;
- example adapters for Codex/`AGENTS.md`, Claude Code/`CLAUDE.md`, Gemini CLI/`GEMINI.md`, and generic agents;
- adoption and convention documentation;
- a repository banner/social-preview design;
- a live AI_CONTEXT implementation in this repository itself;
- explicit documentation of Git-backed, version-controlled memory as a core benefit of the repository-native approach.

The repository was renamed from `AI_Context` to `AI_CONTEXT` to visually match the canonical `AI_CONTEXT.md` file and strengthen the identity of the convention.

## Current Problems

The convention is usable manually, but the optional tooling ecosystem described in the README does not exist yet.

Notable unfinished areas include:

- no initializer CLI such as `ai-context init`;
- no validator/linter for malformed or oversized context files;
- no stale-context detection;
- no secret-scanning integration specific to shared-context files;
- no automated GitHub Action for convention checks;
- no machine-readable optional metadata format;
- no collected real-world adoption examples beyond the projects that originally motivated the pattern;
- no automated tests because the repository currently consists primarily of Markdown conventions, templates, and examples.

The project should avoid adding tooling that makes the Markdown convention dependent on that tooling.

## Recent Changes

- Renamed the repository to `AI_CONTEXT` to align the project name with `AI_CONTEXT.md`.
- Added a visual repository banner.
- Added an MIT License.
- Initialized AI_CONTEXT inside its own repository by adding live project context, project-level agent instructions, an ADR, and a session handoff.
- Added a README section explaining that repository-native memory is also version-controlled, reviewable, attributable, revertible, and historically reconstructable through Git.
- Demonstrated the intended contribution workflow for that documentation change by using a feature branch, separate commits, live-context maintenance, a session handoff, and a pull request rather than editing `main` directly.

## Important Decisions

- AI_CONTEXT is vendor-neutral and repository-native rather than tied to a specific AI agent or provider.
- Durable shared memory is curated engineering context, not raw chat transcripts or hidden chain-of-thought.
- Current state, durable decisions, and session handoffs are separate information layers.
- Tool-specific instruction files are thin adapters into a shared context layer rather than separate competing memories.
- This repository dogfoods AI_CONTEXT while keeping its reusable templates distinct from its own live context. See [`docs/decisions/0001-dogfood-ai-context.md`](decisions/0001-dogfood-ai-context.md).
- Git history is treated as part of the value of the repository-native design: memory changes should remain inspectable and reviewable alongside the project changes they describe.

## Active Work

A documentation pull request is being used to demonstrate how AI_CONTEXT itself should evolve: change the project on a feature branch, update shared context with the change, preserve a useful session handoff, and review the result through a pull request before merging.

## Next Steps

Likely next work includes:

1. Use the live context during real AI_CONTEXT development and refine the convention based on observed friction.
2. Decide whether to build a small initializer CLI and what language/package format should host it.
3. Design a lightweight `ai-context check` validator without making tooling mandatory.
4. Consider optional stale-context and size-budget checks.
5. Add CI/GitHub Action examples once there is something meaningful to validate.
6. Collect real-world examples and compatibility notes from additional coding agents and IDEs.
7. Keep README, convention, adoption guide, templates, examples, and live context synchronized as the format evolves.
8. Consider whether future tooling should expose or summarize context history/diffs without duplicating Git's native capabilities.

## Important Files

- `README.md` — primary public explanation of AI_CONTEXT.
- `AGENTS.md` — live repository-specific agent instructions.
- `docs/AI_CONTEXT.md` — live current-state memory for this repository.
- `docs/CONVENTION.md` — convention definition.
- `docs/ADOPTION.md` — adoption guidance.
- `docs/decisions/` — AI_CONTEXT project's durable decisions.
- `docs/sessions/` — AI_CONTEXT project's development handoffs.
- `templates/AI_CONTEXT.md` — reusable current-state template for adopters.
- `templates/ADR.md` — reusable decision-record template.
- `templates/SESSION.md` — reusable session-handoff template.
- `examples/` — agent-specific and generic integration examples.
- `assets/ai-context-banner.svg` — repository banner displayed in the README.

## Verification Notes

On 2026-08-31, the repository structure and canonical templates were inspected directly from the `main` branch before initializing the live context layer. The live files were created using the repository's own template structure and naming conventions.

For the version-controlled-memory documentation change, work was performed on the `docs/versioned-memory` feature branch. The README and live project context were updated on that branch before opening a pull request, demonstrating that memory changes can be reviewed in the same Git workflow as other repository changes.

There is currently no executable test suite. Validation consists of repository inspection, consistency with the documented convention, and review of the branch diff before merge.

---

Keep this file concise and current. Rewrite stale information instead of endlessly appending history. Move durable rationale into `docs/decisions/` and historical detail into `docs/sessions/`.
