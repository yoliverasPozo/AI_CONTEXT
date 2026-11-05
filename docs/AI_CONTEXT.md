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
- Optional source-only Project adapter: `examples/project_sync/` collects
  bounded GitHub reads or offline snapshots and prints proposals only.
- A separate disabled [single-item writer](PROJECT_WRITER.md) adds one explicitly
  approved PR with complete-state rechecks and local durable receipts. It is not
  installed, scheduled, or invoked by the planner or inbox router.

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
- The inbox router is installed through merged PR #5 and permission fix PR #9.
  PR #8 has successful router runs and a matching `ai-next:chatgpt` marker/label;
  its journal still names Work, so the formal receiving handoff remains conflicted.
- The original Project planner remains read-only. The separate add-only writer
  requires config enablement, explicit execution and exact-digest approval;
  recovery/rollback assessment are read-only. Each new live add requires separate
  exact-operation authorization; implementation alone grants no pending authority.

## Current Problems

- The package is not published to PyPI; installation is from source/GitHub.
- Initialization is not surgical/idempotent for populated projects. Add Work or
  coordination manually; `--force` replaces current context and selected files.
- No context validator, stale-context detection, metadata parser, coordination
  lock, general automatic messaging, or dedicated secret-scanning integration.
- Individual inbox routing and automatic Codex review have live evidence;
  a fully acknowledged, deduplicated autonomous handoff loop remains unverified.
- November 3 live-read acceptance succeeded using existing Windows CLI access;
  archived/unarchived coverage was complete, with no current archived sample.
  A separate writer-reader check read every populated supported field. This
  demonstrates read access, not write permission or live mutation/recovery.
- GitHub has no atomic state comparison/add or creation-ownership flag. Receipts
  cannot prove the writer created an item; automatic rollback is excluded.
- A supervised pilot acknowledged its single add but returned needs_review;
  later read-only reconciliation confirmed expected membership/preservation.
  The original immediate observation/exception was discarded, so its triggering
  predicate remains unknown. This does not establish unattended readiness.
- A later pilot recorded a changed total across immediate post-add pages. Bounded
  fresh-read stabilization merged in PR13 as an experimental opt-in; it does not
  establish the first pilot's lost trigger or permit broader/unattended execution.
- PR13's terminal count mismatch could restart despite a missing approved
  original. A corrective regression/fix is under review; no further pilot is
  prepared. Current GitHub rules do not enforce both AI reviews before merging.
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
- Completed the controlled ChatGPT -> Work -> Codex -> ChatGPT trial
  in [three-agent journal](sessions/2026-10-26-three-agent-roundtrip.md).
  PR #4 was merged on 2026-10-26 as `e7ef9c530bb04fd5a15c8f2298a19228dd33a7ae`.
- Merged the [optional GitHub agent inbox](AGENT_INBOX.md) in PR #5 as
  `5d5bdf9ed775a81355bd18e7e916a9dae9a85ee3`; PR #9's permission fix
  reached main as `8d3b6707fe292662ca879dd399b3c53aee632030`.
- Added an experimental [central Project proposal adapter](PROJECT_SYNC.md),
  guarded live reads, generic offline fixtures and handoff-conflict rules.
- PR #10 merged as `d0c9cbf770d12d505b08210c3ed42f9ae0cded4b`.
  November 3 adds a disabled add-only writer, complete-state receipts, bounded
  one-attempt recovery and guarded manual rollback assessment; see the
  [implementation session](sessions/2026-11-03-add-only-project-writer.md).
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
- Project fields remain derived views, never authorization. The planner stays
  plan-only under [ADR 0005](decisions/0005-central-project-projection.md);
  [experimental ADR 0006](decisions/0006-disabled-add-only-project-writer.md)
  bounds the separate writer. No schedule or routing changes are included.

## Active Work

- Writer PR11 is merged at `451c7c8c9315a59fdff838e37d6f9b6b80e1b5c6`.
  Diagnostic PR12 merged at `4e506b29ae458cb138b0b719d8cf9607e68deb5f`.
  PR13 stabilization merged as `c4d9fa2ae8d85fc99befdddc787bd9f4aa3edf19`;
  117 tests and all four exact-main CI jobs passed. Reusing
  `fix/project-readback-stabilization` for the terminal missing-original correction:
  terminal guard added and archive-state fixtures corrected after PR Lens review.
  Both missing-original cases reproduce the prior defect and pass on PR14, along
  with all 118 tests. No eligible missing PR found for another timed pilot; original
  receipts stay immutable. See the [corrective session](sessions/2026-11-04-terminal-original-preservation.md),
  [review-gate proposal](reviews/2026-11-04-review-completion-gate.md),
  [session](sessions/2026-11-04-verification-stabilization.md),
  [ADR0007](decisions/0007-bounded-post-add-readback.md) and
  [next-pilot criteria](PROJECT_WRITER_DIAGNOSTICS.md). New pilots require separate
  source/state/expiry authority; the prior operation is permanently spent.
- [PR #8](https://github.com/yoliverasPozo/AI_CONTEXT/pull/8) remains open at
  `44ef97da3786d30905bb341903bb7b12dc955ff5` for a read-only routing trial.
  Its [exact-head handoff](https://github.com/yoliverasPozo/AI_CONTEXT/blob/44ef97da3786d30905bb341903bb7b12dc955ff5/docs/sessions/2026-10-27-inbox-work-event-smoke.md)
  says `ready`, next owner ChatGPT Work, while marker/label say ChatGPT.
  Preserve this synthetic-transition conflict; no receiving acknowledgment is
  published. Its Active Work discovery review finding remains unresolved on
  that PR. The trial is not approved for merge or implementation.
- PR #7's automatic review completed at `e06adb31470c585209069a6f1416001c57d04475`
  with trigger `New commits`; PR #8's review says `PR opened`. PR #6's review
  at `513167c3b50e80da1d64766767119c37f3af8140` was manually requested.
  These review experiments are separate from implementation handoff acceptance.
- The prior [three-agent trial](sessions/2026-10-26-three-agent-roundtrip.md)
  is complete and merged in PR #4. ADR 0003 remains experimental.

## Next Steps

1. Review the disabled add-only writer and its exact-head/state/receipt tests.
   A single-item pilot needs a fresh private proposal and explicit owner approval;
   use existing credentials only. Recurring activation remains a separate stage.
2. Resolve PR #8's journal/marker conflict through its owner. Independently
   verify canonical watcher configuration, quiet deduplication and a published
   receiving acknowledgment. Keep ADRs 0003/0004/0005 experimental.
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
- `docs/PROJECT_SYNC.md`, `examples/project_sync/`: optional plan-only Project adapter.
- `docs/PROJECT_WRITER.md`, `examples/project_sync/writer*.py`: separate disabled
  add-only writer and read-only recovery/rollback assessment.

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

2026-11-02 live inspection confirmed installed router successes
[40577601856](https://github.com/yoliverasPozo/AI_CONTEXT/actions/runs/40577601856)
and [40580597743](https://github.com/yoliverasPozo/AI_CONTEXT/actions/runs/40580597743).
Saved account-side watcher reports indicate individual Work event receipt and
later ChatGPT discovery, but are not published repository acknowledgments or
independent proof of current scheduler settings. The central prototype's local
tests and sanitized live-read limitation are recorded in its dated session;
no Project write or schedule was installed.
