# Decision: Implement the initial CLI in Python with no runtime dependencies

Date: 2026-08-31
Status: Accepted

## Context

AI_CONTEXT is currently a Markdown convention and reference repository. The next milestone is an optional initializer command, `ai-context init`, that can scaffold the shared-memory structure in an existing Git repository.

The CLI must support the convention without becoming a prerequisite for it. It should be easy to understand, portable across common developer environments, safe around existing repository files, and straightforward to test. It should not require an AI provider, network access, or framework-specific runtime.

The repository also needs a packaging model that can later support convenient invocations such as `pipx`, `uvx`, or ordinary `pip` installation if the project is published to a Python package index.

## Decision

Implement AI_CONTEXT CLI v0.1 as a Python 3.10+ package with:

- distribution name `ai-context`;
- import package `ai_context`;
- console entry point `ai-context`;
- standard-library-only runtime code;
- no LLM calls and no network dependency;
- `setuptools` as the build backend;
- bundled copies of the canonical context/adaptor Markdown resources required by `init`;
- tests that verify those bundled resources remain byte-for-byte synchronized with the repository's canonical `templates/` and `examples/` files.

The initial command is `ai-context init`. It will detect the Git repository root, create the core `docs/AI_CONTEXT.md`, `docs/decisions/`, and `docs/sessions/` structure, and optionally install selected agent adapters.

The core initialization remains vendor-neutral. Agent-specific adapters are opt-in rather than implicitly choosing a preferred AI provider.

The CLI must refuse to overwrite managed files unless the user explicitly supplies `--force`.

## Alternatives Considered

### Node.js / npm

Node would provide familiar `npx` distribution and strong cross-platform support. It was not selected for v0.1 because the initial functionality is primarily filesystem and argument-processing logic, for which Python's standard library is sufficient. Choosing Node would not materially improve the convention itself.

### Go single binary

Go could eventually provide excellent standalone binary distribution. It was not selected for v0.1 because it introduces a larger implementation/build step before the project has validated whether the CLI interface is stable enough to justify compiled releases.

### Shell scripts

Shell would minimize project structure, but cross-platform behavior—especially Windows support—would be weaker and safe filesystem handling/testing would be less consistent.

### AI-generated initialization

The CLI could call an LLM to inspect the repository and populate `AI_CONTEXT.md`. This was rejected for v0.1 because it would introduce provider dependencies, credentials, network requirements, cost, and model-specific behavior into a convention intended to remain vendor-neutral. The initializer scaffolds the memory layer; the user's chosen agent can populate it afterward.

## Rationale

Python provides a small implementation surface, strong standard-library support for filesystem and CLI operations, straightforward unit testing, and several future distribution options without introducing runtime dependencies.

Keeping model inference outside the CLI preserves a clean architectural boundary:

> The CLI scaffolds the memory system; AI agents and humans create and maintain the memory.

Bundling the reference Markdown resources makes the installed CLI self-contained, while synchronization tests prevent the bundled copies from silently drifting from the canonical repository files.

## Consequences

Benefits:

- v0.1 can run without network access, API keys, or third-party runtime libraries;
- the CLI remains optional and does not redefine the underlying Markdown convention;
- behavior is deterministic and testable;
- future publication can support common Python installation tools;
- agent adapters remain explicit and vendor-neutral at the core.

Costs and risks:

- users without Python need another installation path;
- bundled Markdown resources duplicate canonical repository files and therefore require synchronization checks;
- package publication, signed releases, standalone binaries, and additional distribution channels remain future work;
- the CLI interface may need refinement after real-world dogfooding.

Follow-up work:

- implement and dogfood `ai-context init`;
- add automated tests/CI for the executable code;
- document local installation and usage;
- evaluate packaging/distribution after the command interface has seen real-world use;
- consider `ai-context check` only after initializer behavior is stable.

## Supersedes / Superseded By

None.

---

Create an ADR only when a decision is important enough that a future developer or AI agent might otherwise revisit, reverse, or misunderstand it.
