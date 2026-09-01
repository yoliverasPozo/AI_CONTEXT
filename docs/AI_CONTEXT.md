# Project Context

## Project Goal

AI_CONTEXT defines and demonstrates a lightweight, vendor-neutral, repository-native shared-memory pattern for AI-assisted software projects.

The project aims to let humans and different AI coding agents preserve and recover the useful engineering state of a project without depending on any single chat history or model context window.

The repository should serve both as:

1. a clear explanation and reusable reference implementation of the convention; and
2. a real project that uses AI_CONTEXT on itself so future development demonstrates the workflow in practice.

## Current Architecture

The repository is organized into three layers:

### Reference layer

- `README.md` — public introduction, rationale, workflow, CLI usage, and high-level documentation.
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

### Optional tooling layer

- `pyproject.toml` — Python package metadata and the `ai-context` console entry point.
- `src/ai_context/` — standard-library-only CLI implementation.
- `src/ai_context/resources/` — bundled copies of the canonical Markdown resources required by the installed CLI.
- `tests/` — unit tests for initialization behavior and resource synchronization.
- `.github/workflows/tests.yml` — cross-platform CI on supported Python versions.

The tooling layer supports the Markdown convention but is not required to use it.

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
- explicit documentation of Git-backed, version-controlled memory as a core benefit of the repository-native approach;
- `ai-context` CLI v0.1 with the `init` command;
- automated unit tests and GitHub Actions CI for the executable tooling.

`ai-context init` detects the Git repository root, creates `docs/AI_CONTEXT.md`, `docs/decisions/`, and `docs/sessions/`, and can optionally install selected agent adapters. It supports `--dry-run` and explicit `--force` overwrite behavior and does not call an LLM or require network access at runtime.

The repository was renamed from `AI_Context` to `AI_CONTEXT` to visually match the canonical `AI_CONTEXT.md` file and strengthen the identity of the convention.

## Current Problems

The convention and initializer are usable, but the optional tooling ecosystem is intentionally still small.

Notable unfinished areas include:

- the `ai-context` package is not yet published to PyPI or another package registry;
- v0.1 treats existing managed files as conflicts and aborts unless `--force`; it does not yet support surgical/idempotent operations such as adding one adapter while preserving an already-populated `docs/AI_CONTEXT.md`;
- no `ai-context check` validator/linter;
- no stale-context or context-size detection;
- no secret-scanning integration specific to shared-context files;
- no machine-readable optional metadata format;
- no collected real-world adoption examples beyond the projects that originally motivated the pattern.

The project should avoid adding tooling that makes the Markdown convention dependent on that tooling.

## Recent Changes

- Renamed the repository to `AI_CONTEXT` to align the project name with `AI_CONTEXT.md`.
- Added a visual repository banner.
- Added an MIT License.
- Initialized AI_CONTEXT inside its own repository by adding live project context, project-level agent instructions, an ADR, and a session handoff.
- Added a README section explaining that repository-native memory is also version-controlled, reviewable, attributable, revertible, and historically reconstructable through Git.
- Demonstrated the intended contribution workflow through feature branches, separate commits, live-context maintenance, session handoffs, pull-request review, and merge.
- Added ADR 0002 selecting Python 3.10+ with no runtime dependencies for the initial optional CLI.
- Implemented `ai-context init` v0.1 with optional Codex, Claude, Gemini, and generic adapters.
- Added unit tests, packaged-resource synchronization checks, and cross-platform GitHub Actions CI.
- Added README installation and usage documentation for CLI v0.1.

## Important Decisions

- AI_CONTEXT is vendor-neutral and repository-native rather than tied to a specific AI agent or provider.
- Durable shared memory is curated engineering context, not raw chat transcripts or hidden chain-of-thought.
- Current state, durable decisions, and session handoffs are separate information layers.
- Tool-specific instruction files are thin adapters into a shared context layer rather than separate competing memories.
- This repository dogfoods AI_CONTEXT while keeping its reusable templates distinct from its own live context. See [`docs/decisions/0001-dogfood-ai-context.md`](decisions/0001-dogfood-ai-context.md).
- Git history is treated as part of the value of the repository-native design: memory changes should remain inspectable and reviewable alongside the project changes they describe.
- CLI v0.1 is Python 3.10+, standard-library-only at runtime, model-independent, and optional. See [`docs/decisions/0002-python-cli-v0.1.md`](decisions/0002-python-cli-v0.1.md).
- The CLI scaffolds the memory system; AI agents and humans create and maintain the memory.

## Active Work

The immediate work is to dogfood `ai-context init` in real repositories and use observed friction to refine the initializer before expanding the tooling surface.

Substantial changes should continue through normal Git branches and pull requests so the repository itself remains a practical demonstration of version-controlled shared memory.

## Next Steps

Likely next work includes:

1. Dogfood `ai-context init` in multiple existing repositories and record usability problems.
2. Improve idempotent/surgical initialization so an existing AI_CONTEXT project can safely add or refresh individual adapters without overwriting its live context.
3. Decide when and how to publish/install signed versioned releases beyond direct GitHub installation.
4. Design a lightweight `ai-context check` validator without making tooling mandatory.
5. Add stale-context and context-size checks after the validator contract is clear.
6. Consider secret-scanning integration for shared-context files.
7. Collect real-world examples and compatibility notes from additional coding agents and IDEs.
8. Consider whether future tooling should expose or summarize context history/diffs without duplicating Git's native capabilities.

## Important Files

- `README.md` — primary public explanation and CLI usage documentation.
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
- `src/ai_context/cli.py` — CLI parsing, Git-root detection, safety checks, and initialization behavior.
- `src/ai_context/resources/` — bundled canonical resources used by the installed CLI.
- `tests/test_cli.py` — initializer behavior tests.
- `tests/test_resources.py` — bundled-resource synchronization test.
- `.github/workflows/tests.yml` — Linux/Windows and Python 3.10/3.13 CI matrix.
- `pyproject.toml` — Python package metadata and console entry point.
- `assets/ai-context-banner.svg` — repository banner displayed in the README.

## Verification Notes

On 2026-08-31, CLI v0.1 was validated locally before being committed:

- `python -m unittest discover -s tests -v` passed 11 tests;
- the package installed successfully in editable mode with no runtime dependencies;
- `ai-context --version` reported `0.1.0`;
- `ai-context init --agents codex,gemini` created the expected core context structure and adapters in a temporary Git repository;
- a second initialization attempt exited with code 1 and refused to overwrite the existing managed files.

GitHub Actions is configured to repeat package installation, unit tests, and a CLI smoke test on Linux and Windows with Python 3.10 and 3.13 for pull requests and pushes to `main`.

---

Keep this file concise and current. Rewrite stale information instead of endlessly appending history. Move durable rationale into `docs/decisions/` and historical detail into `docs/sessions/`.
