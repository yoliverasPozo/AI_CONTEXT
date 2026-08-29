# Adopting AI_Context

AI_Context works best when introduced as a **small shared-memory convention**, not as a requirement to document every AI interaction.

## 1. Add the shared memory structure

Copy the templates into the project:

```text
docs/
├── AI_CONTEXT.md
├── decisions/
└── sessions/
```

Use:

- `templates/AI_CONTEXT.md` for the living project state;
- `templates/ADR.md` for durable decisions;
- `templates/SESSION.md` for substantial-work handoffs.

Do not create empty decision or session files merely to satisfy the structure.

## 2. Add an agent-native entry point

Choose the instruction mechanism your coding agent reads automatically:

- Codex: `AGENTS.md`
- Claude Code: `CLAUDE.md`
- Gemini CLI: `GEMINI.md`
- other tools: their repository instruction file or a startup prompt

Keep this adapter short. It should tell the agent **where the shared memory lives, when to read it, and when to maintain it**.

Avoid duplicating the project's durable context separately in every vendor-specific file.

## 3. Initialize `AI_CONTEXT.md` from reality

Do not ask an agent to invent a project summary from memory alone.

Have it inspect the repository first, including as appropriate:

- README and user documentation;
- source tree;
- package/dependency files;
- configuration;
- tests;
- CI/CD workflows;
- deployment manifests;
- current Git state;
- recent commits or pull requests;
- observable runtime state when available.

Then summarize only what the evidence supports.

## 4. Establish an authority order

Recommended default:

```text
current code/config/tests/runtime
        ↓
accepted ADRs
        ↓
AI_CONTEXT.md
        ↓
recent session handoffs
        ↓
conversation memory
```

Why put ADRs above `AI_CONTEXT.md`? A living summary can become stale accidentally, while an accepted decision record explicitly documents an architectural choice until it is superseded.

The actual implementation and observed behavior still win when documentation and reality diverge; that divergence should then be fixed.

## 5. Define what counts as substantial work

A project should not create a journal for every interaction.

Useful triggers include:

- debugging that required meaningful investigation;
- architecture or API design;
- migrations;
- significant refactors;
- deployment incidents;
- multiple attempted approaches;
- important stakeholder decisions;
- work intentionally left incomplete;
- a discovery likely to save future work.

Tiny formatting changes, typo fixes, mechanical renames, or trivial edits usually need no session record.

## 6. Keep the current-state file small

`AI_CONTEXT.md` should optimize for **recovery speed**.

A new agent should be able to read it quickly and know where to look next.

When it grows too large:

- delete obsolete information;
- move durable rationale into ADRs;
- leave historical detail in session files;
- link rather than duplicate;
- summarize old recent changes into the current state.

A project-specific size budget can be useful, but AI_Context intentionally does not mandate one universal token or line limit.

## 7. Treat Git review as memory review

Context changes can be wrong just like code changes.

Review them for:

- stale claims;
- accidental secrets;
- speculation presented as fact;
- decisions recorded without agreement;
- duplicated information;
- missing test evidence;
- outdated next steps.

When practical, commit context updates with the implementation they describe. This makes historical reconstruction much easier.

## 8. Separate shared and private memory

AI_Context is for information that belongs with the project.

Do not use it as a substitute for private agent memory, secret management, credentials, or personal notes.

If a fact should not be visible to everyone who can read the repository, it does not belong in the shared layer.

## 9. Recover after a context reset

A fresh agent can be prompted with something as small as:

```text
Read the repository instructions and shared AI context. Review relevant
accepted decisions and recent session handoffs, inspect the current Git and
source state, and reconstruct what is complete, unresolved, and next before
continuing.
```

The repository should provide enough evidence that the agent does not need the previous chat transcript.

## 10. Evolve the convention carefully

Start with Markdown before adding automation or schemas.

Add tooling only when a real problem appears, such as:

- context files becoming too large;
- required sections frequently missing;
- stale references accumulating;
- multiple repositories needing automated initialization;
- teams wanting CI checks;
- machine-readable metadata becoming genuinely useful.

The goal is durable continuity, not documentation bureaucracy.

## Suggested rollout for an existing repository

1. Copy the three templates.
2. Add one native agent adapter.
3. Ask an agent to inspect the repository and initialize `AI_CONTEXT.md`.
4. Review the result manually.
5. Convert only the most important existing architectural choices into ADRs.
6. Start session journals with the next substantial work session rather than reconstructing every historical chat.
7. Adjust the rules after seeing how the team actually uses them.

That is enough to get most of the benefit without turning adoption into a migration project.
