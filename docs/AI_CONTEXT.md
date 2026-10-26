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
- Merged into `main` through [PR #3](https://github.com/yoliverasPozo/AI_CONTEXT/pull/3)
  on 2026-10-26 as `fb092b6ba13d10a977a43d194f6945fce6b1908d`:
  `--coordination` installs shared
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
- Work capabilities vary per session. The three-agent GitHub handoff trial has
  passed its initial independent review, but automatic cross-chat transfers,
  instruction discovery, and broad real-project use remain untested.
- Coordination v1 remains experimental under ADR 0003 after PR #3's merge;
  one controlled documentation round-trip is evidence, not full validation.

## Recent Changes

- Merged PR #3's optional coordination protocol and explicit-transfer template while
  preserving the original context, ADR, and session structures.
- Added a Work startup/return adapter, opt-in CLI support, packaged resources,
  compatibility/safety tests, and manual adoption guidance for existing projects.
- Updated thin agent adapters to discover coordination instructions when present.
- Completed the controlled ChatGPT -> Work -> Codex -> ChatGPT handoff review
  in [three-agent trial](sessions/2026-10-26-three-agent-roundtrip.md), draft PR #4.
  The receiving acknowledgments and validation are published; merge is pending user approval.
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

- Three-agent coordination trial: branch `trial/three-agent-roundtrip-2026-10-26`;
  status `complete` for its controlled handoff and independent review, with
  [draft PR #4](https://github.com/yoliverasPozo/AI_CONTEXT/pull/4) **unmerged**.
  Work, Codex and ChatGPT acknowledgments and validation are in the
  [trial journal](sessions/2026-10-26-three-agent-roundtrip.md).
  Next action: user separately decides whether to merge PR #4. No deployment
  is authorized. ADR 0003 remains experimental.

## Next Steps

1. Decide whether to merge draft PR #4 after the successful controlled handoff;
   final merge is not included in the trial authorization.
2. Trial the protocol in a non-sensitive existing project before reconsidering
   experimental ADR 0003; avoid mandatory metadata without a new decision.
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

Historical PR #3 evidence in the
[implementation journal](sessions/2026-10-26-agent-coordination-work.md):
on 2026-10-26, the clean baseline passed 11 tests on Windows/Python 3.13.5.
The expanded suite passed 18 tests after the new tests exposed the absent flag,
adapter, and packaged resources. A built wheel installed in an isolated
environment passed CLI/output, dry-run, and conflict checks for core, existing
adapters, coordination, and Work selections. Relative Markdown links/anchors,
whitespace, and public-data patterns were checked. Review and CI evidence
belongs in that implementation journal. Those results do not validate PR #4.
Work's documentation checks and receiving acknowledgment are recorded in the
[trial journal](sessions/2026-10-26-three-agent-roundtrip.md), followed by Codex's
independent tests, link/whitespace checks, and revision-specific Actions evidence.
ChatGPT independently verified both receiving acknowledgments and the two-file
scope at PR head `fa486ff2840c15173d8296761a570bf836ed593b`; GitHub Actions
run 40400477647 passed 4/4 jobs on that revision. The final review is recorded
in the trial journal. Subsequent documentation-only commits need their own CI
confirmation and do not change the already-verified implementation.
