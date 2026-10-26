# Session: Optional agent coordination and ChatGPT Work integration

Date: 2026-10-26

## Coordination

Protocol: AI_CONTEXT coordination v1
Task ID: 2026-10-26-agent-coordination-work
Status: active
Current owner: Codex implementer
Next owner: User / PR reviewer
Updated: 2026-10-26 (America/La_Paz; see Git/PR timestamps for publication)
Repository: yoliverasPozo/AI_CONTEXT
Base branch: main
Work branch: feat/agent-coordination-work
Last inspected commit: 81f9f0f (main baseline; implementation in working tree)
Last tested commit: working tree based on 81f9f0f; final published SHA pending
Pull request: not yet opened; draft requested
Continuation of: none

### Acknowledgment / transfer history

- 2026-10-26 (America/La_Paz): Codex implementer accepted the user-authorized
  task; inspect the actual repository, implement on a separate branch, validate,
  and open a draft PR. Transfer to review remains pending publication.

## Goal

Implement a backward-compatible agent coordination/handoff protocol with
practical ChatGPT Work instructions and templates in the existing public repo.
Preserve AGENTS.md, current-state context, ADR/session conventions, and vendor
neutrality. Keep public records free of sensitive material.

### Scope and authorization

- Authorized: inspect, implement, check, create a separate branch, publish a
  draft PR, and report files, evidence, URL, and uncertainties.
- Not authorized: merge or deployment. No messages to other user-owned chats
  or external recipients are part of this task.
- Acceptance: optional protocol and Work transfer/return instructions are
  usable; existing default initializer behavior and file protections remain;
  tests and packaged resources are checked; reviewable draft PR is published.

## Investigation

- Read the actual root instructions, live context, both accepted ADRs, recent
  CLI/session history, convention/adoption docs, canonical templates/adapters,
  Python implementation, tests, packaging, and cross-platform CI definition.
- Confirmed that generic templates/examples and live project memory are
  intentionally distinct, and that CLI resources are bundled and sync-tested.
- The initializer preflights all managed-file conflicts before writes, supports
  dry-run and explicit force, and has no surgical existing-project update mode.
- Existing session records already serve handoffs; a separate Work memory or
  task directory would duplicate that layer.
- Product-specific native environment transfers are separate from this
  repository protocol. Reference documentation inspected:
  [Remote connections](https://learn.chatgpt.com/docs/remote-connections) and
  [Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees).
  This work makes no live Work capability or chat-visibility claim.

## Decisions

- Trial optional coordination v1 in shared Markdown; retain all core paths,
  existing template headings, dated session names, and ADR numbering.
- Add ownership/status, scope, revision/evidence, acknowledgment, and next-action
  fields as an optional extension to sessions. Ownership is advisory, not a lock.
- Work uses a thin startup/return prompt, explicit task pointers, capability
  checks, and a reviewed unpublished-text fallback when writing is unavailable.
- `--coordination` installs the protocol and handoff form; `--agents work`
  includes them automatically. Existing options remain compatible. Manual
  additive adoption avoids force-replacing populated project context.
- Keep ADR 0003 experimental pending review and real use. See
  [ADR 0003](../decisions/0003-optional-agent-coordination.md).

## Changes Made

- `docs/COORDINATION.md`: shared lifecycle, start/resume/transfer, ownership,
  stale-revision/concurrency, limited-access Work, and public-sharing rules.
- `templates/HANDOFF.md`: optional extended session form preserving established
  sections; `templates/SESSION.md`, `templates/AI_CONTEXT.md`, and `templates/ADR.md`
  remain unchanged.
- `examples/CHATGPT_WORK.md`: startup and return prompts; existing adapters gain
  conditional discovery of shared coordination instructions.
- `src/ai_context/cli.py`: opt-in flag, Work adapter, supporting-file selection,
  and explicit instruction to deliver the Work prompt. No runtime dependencies.
- `src/ai_context/resources/`: synchronized new and existing adapter resources.
- `tests/test_cli.py`, `tests/test_resources.py`: compatibility, opt-in outputs,
  Work support, conflicts, dry-run, force scope, CLI parsing, and resource sync.
- `README.md`, `docs/CONVENTION.md`, `docs/ADOPTION.md`: optional usage and safe
  manual adoption in populated projects.
- `AGENTS.md`, `docs/AI_CONTEXT.md`, ADR 0003, and this journal: live continuity.

## Tests and Validation

- Baseline: editable installation succeeded; `python -m unittest discover -s
  tests -v` passed all 11 original tests on Windows / Python 3.13.5.
- Test-first check: new cases exposed missing `--coordination`, unknown `work`
  adapter, absent API option, and unbundled resources. These were expected
  pre-implementation failures, not a baseline regression.
- Final local suite: `python -m unittest discover -s tests -v` passed 18 tests,
  including all original tests, on Windows / Python 3.13.5.
- `python -m pip wheel . --no-deps --wheel-dir <scratch-wheel-directory>` built
  the wheel. Installed it with `pip install --no-deps` in an isolated environment
  and invoked its installed entry point from outside the source checkout.
  Core-only, all original adapters, coordination-only, and Work+Codex selections
  produced the exact expected files; dry-run made no writes; repeat init refused
  overwrites and preserved file bytes. Help/version and site-packages isolation
  checks passed. No source-checkout resources were needed at runtime.
- Checked 30 Markdown files: all 34 relative links/anchors resolved and no
  duplicate level-2 sections were found. `git diff --check` passed.
- Public-data pattern scan of 24 changed/new files passed; manual inspection
  supplemented it. This is a scoped check, not a general secret scanner.
- Independent read-only review found no material or minor issues requiring
  fixes and no declined-to-judge items. The reviewer independently repeated all
  18 tests, checked whitespace, wheel resources, and installation isolation.
  Remote CI results will be recorded after publication.

## Problems Encountered

- Referenced conversation retrieval exposed only bounded user messages and
  unresolved assistant-content references. The current explicit user request
  and actual repository were used as the implementation requirements; no
  missing prior assistant proposal was treated as authoritative.
- No live Work round-trip was attempted; permissions and available instruction
  surfaces must be checked in the actual receiving session.
- Populated-project initialization still aborts on conflicts. Surgical updates
  were deliberately kept out of scope rather than weakening overwrite safety.

## Current Result

Implementation and local verification/review are complete on the feature branch.
Publication and user review acknowledgment are not yet complete. Do not
interpret this record as a merge or a live Work integration test.

## Next Steps

1. Codex implementer: publish the branch and draft PR, record its revision and
   CI status, then transfer the task to user review.
2. User / reviewer: inspect the published PR; no merge is authorized in this task.
3. After review, trial a sanitized Work transfer and return using the same
   handoff pointers; record any capability or workflow friction.
