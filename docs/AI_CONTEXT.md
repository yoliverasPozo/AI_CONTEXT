# Project Context

## Project Goal

Define and demonstrate a lightweight, vendor-neutral, repository-native shared
memory pattern so humans and AI agents can continue work without private chat
history. The repository is both a reusable reference and a live example.

## Current Architecture

- Reference: `README.md`, `docs/CONVENTION.md`, `docs/ADOPTION.md`, generic
  `templates/`, and thin agent adapters in `examples/`.
- Live memory: project instructions in `AGENTS.md`, this current-state summary,
  numbered ADRs in `docs/decisions/`, and dated journals in `docs/sessions/`.
- Optional tooling: Python 3.10+, standard-library-only `ai-context init`;
  bundled Markdown in `src/ai_context/resources/` is checked against canonical
  reference files. No model calls or network access at runtime.
- Optional coordination: `docs/COORDINATION.md` defines shared task transfers.
  `templates/HANDOFF.md` extends existing session records; Work's adapter uses
  the same records. This adds no mandatory directory, service, or task database.
- Git versions memory with the implementation; PRs review both together.

## Current State

- Public MIT-licensed Markdown convention, context/ADR/session templates,
  adoption guidance, and a live instance of the convention in this repository.
- CLI v0.1 initializes the core context structure with optional Codex, Claude,
  Gemini, and generic adapters; detects repository roots and supports dry-run
  and explicit force overwrite. Existing managed files abort before writes.
- On the coordination feature branch, `--coordination` installs shared
  instructions and `docs/HANDOFF_TEMPLATE.md`; `--agents work` also installs
  `AI_CONTEXT_WORK.md` and includes those supporting files. Existing default
  output paths and existing adapter selections retain their behavior.
- The optional protocol covers ownership/status, authorized scope, revision
  pointers, acknowledgment, checks, blockers, concurrent work, and publication.
  Work instructions include read-only/no-access fallback and return prompts.
- Unit tests and GitHub Actions cover initializer behavior and resource sync.

## Current Problems

- The package is not published to PyPI; installation is from source/GitHub.
- Initialization is not surgical/idempotent for populated projects. Add Work or
  coordination manually; `--force` replaces current context and selected files.
- No context validator, stale-context detection, metadata parser, coordination
  lock, automatic messaging, or dedicated secret-scanning integration.
- Work capabilities vary per session; no live Work round-trip has been tested.
  The protocol does not guarantee automatic adapter discovery or chat access.
- Coordination v1 is experimental and awaits review and real-project use.

## Recent Changes

- Added an optional coordination protocol and explicit-transfer template while
  preserving the original context, ADR, and session structures.
- Added a Work startup/return adapter, opt-in CLI support, packaged resources,
  compatibility/safety tests, and manual adoption guidance for existing projects.
- Updated thin agent adapters to discover coordination instructions when present.
- Earlier milestones established dogfooding, Git-versioned memory, and the
  dependency-free Python initializer; see ADRs and prior session journals.

## Important Decisions

- Shared memory is curated engineering context, not secrets, raw transcripts,
  private conversation identifiers, or hidden chain-of-thought.
- Current observable repository/runtime evidence precedes accepted ADRs,
  current context, sessions, and conversation memory for factual conflicts.
  This order never overrides current user instructions or permissions.
- Generic reference material stays separate from live project memory. See
  [ADR 0001](decisions/0001-dogfood-ai-context.md).
- Python 3.10+ with no runtime dependencies; tooling scaffolds memory and
  humans/agents maintain it. See [ADR 0002](decisions/0002-python-cli-v0.1.md).
- Coordination remains optional, uses existing sessions, and treats ownership
  as advisory. Work is a thin adapter, not a separate memory layer. See
  [experimental ADR 0003](decisions/0003-optional-agent-coordination.md).

## Active Work

- Coordination v1 / Work integration: Codex implementer; branch
  `feat/agent-coordination-work`; status `review` in
  [draft PR #3](https://github.com/yoliverasPozo/AI_CONTEXT/pull/3), with no merge
  authorized. Next owner: user / PR reviewer (acknowledgment pending).
  Handoff: [2026-10-26 session](sessions/2026-10-26-agent-coordination-work.md).
  Inspect branch/PR state before continuing; this branch summary is not proof
  of merge or current ownership.

## Next Steps

1. Review the coordination draft PR and trial a sanitized transfer into and
   back from an actual Work session with its available tools.
2. Use that feedback to revise the protocol and decide whether ADR 0003 can
   become accepted; do not add mandatory metadata without a new decision.
3. Improve surgical/idempotent initialization for existing repositories.
4. Dogfood initialization, plan package distribution, and consider a lightweight
   validator, stale-context checks, and secret scanning after real use.

## Important Files

- `AGENTS.md`, `docs/AI_CONTEXT.md`, `docs/decisions/`, `docs/sessions/`: live memory.
- `README.md`, `docs/CONVENTION.md`, `docs/ADOPTION.md`: public usage and conventions.
- `docs/COORDINATION.md`: optional shared handoff instructions, also bundled.
- `templates/AI_CONTEXT.md`, `templates/ADR.md`, `templates/SESSION.md`: core templates.
- `templates/HANDOFF.md`: optional transfer template, bundled as `HANDOFF.md`.
- `examples/CHATGPT_WORK.md`: Work startup/return prompt, bundled for installation.
- `examples/`: thin adapters; `src/ai_context/resources/`: synchronized copies.
- `src/ai_context/cli.py`, `pyproject.toml`: initializer and packaging.
- `tests/`, `.github/workflows/tests.yml`: local and cross-platform CI checks.
- `assets/ai-context-banner.svg`: README banner.

## Verification Notes

On 2026-10-26, the clean baseline passed 11 tests on Windows/Python 3.13.5.
The expanded suite passed 18 tests after the new tests exposed the absent flag,
adapter, and packaged resources. A built wheel installed in an isolated
environment passed CLI/output, dry-run, and conflict checks for core, existing
adapters, coordination, and Work selections. Relative Markdown links/anchors,
whitespace, and public-data patterns were checked. Review and CI evidence
belongs in the linked session handoff. No live Work trial is claimed.
