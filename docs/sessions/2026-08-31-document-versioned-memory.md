# Session: Document version-controlled memory

Date: 2026-08-31

## Goal

Document a core benefit of AI_CONTEXT that became clear while using the convention: because shared project memory lives in the Git repository, the memory itself is versioned and its evolution can be reviewed over time.

The change was also intentionally performed through a normal feature-branch and pull-request workflow to demonstrate how AI_CONTEXT memory should evolve alongside the rest of a project.

## Investigation

The existing README already described AI_CONTEXT as Git-native, auditable, and repository-native, but it did not explicitly explain the consequences of keeping memory in Git history.

The live `docs/AI_CONTEXT.md` and project-specific `AGENTS.md` were reviewed before making the change, following the repository's own AI_CONTEXT workflow.

The missing concept was identified as more than simple persistence. Git provides project memory with:

- historical versions;
- diffs;
- review through pull requests;
- attribution through commit history and blame;
- rollback;
- correlation between context and implementation changes; and
- reconstruction of the project's shared understanding at older commits.

## Decisions

- Treat version-controlled memory as a first-class benefit of AI_CONTEXT rather than a minor implementation detail.
- Explain the concept prominently in the README under its own `Version-controlled memory` section.
- Do not create a new ADR for this change because it follows directly from the existing repository-native/Git-native design rather than changing the convention's architecture.
- Update the live `docs/AI_CONTEXT.md` and create this session handoff so the documentation change itself demonstrates the convention.
- Perform the work on `docs/versioned-memory` and submit it through a pull request instead of changing `main` directly.

## Changes Made

- `README.md`
  - Added a dedicated `Version-controlled memory` section.
  - Explained history, diffs, review, attribution, rollback, code/context correlation, historical reconstruction, and "memory archaeology."
  - Added the concise framing: AI_CONTEXT turns project memory into a shared, auditable, version-controlled artifact of the repository.

- `docs/AI_CONTEXT.md`
  - Added versioned memory to the current architecture/state.
  - Recorded this change and the PR-based demonstration workflow.
  - Updated active work, next steps, and verification notes.

- `docs/sessions/2026-08-31-document-versioned-memory.md`
  - Added this handoff.

## Tests and Validation

This repository currently has no executable test suite for documentation changes.

Validation for this work consists of:

- inspecting the existing README and live AI_CONTEXT before editing;
- making all changes on the `docs/versioned-memory` feature branch;
- comparing the branch against `main` before merge;
- reviewing the resulting pull-request diff for scope and consistency.

## Problems Encountered

No product or convention problem was discovered during the documentation change.

The work reinforced an important practical property of the pattern: context updates can be reviewed and corrected using the same Git workflow as code, rather than being hidden inside an AI conversation.

## Current Result

The feature branch documents version-controlled memory in the README and updates AI_CONTEXT's own live memory to reflect the change.

The branch is intended to be reviewed and merged through a pull request, leaving the Git history itself as a concrete example of the concept being described.

## Next Steps

- Review the pull request diff.
- Merge the PR if the documentation is clear and scoped correctly.
- After merge, continue using feature branches and context updates for future substantial AI_CONTEXT work.
- Consider whether future `ai-context` tooling should provide convenient views of context-history changes while relying on Git as the authoritative history store.

---

Create session records only for substantial work. Preserve useful engineering context, not raw chat transcripts or hidden chain-of-thought.
