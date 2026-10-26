# Decision: Add an optional shared coordination protocol

Date: 2026-10-26
Status: Experimental

## Context

Project facts can survive in AI_CONTEXT while task ownership and continuation
instructions remain trapped in individual chats. ChatGPT Work needs a practical
entry point and a return path that also works when a session cannot write to a
repository or read another conversation. This public reference repository must
preserve its vendor-neutral core, lightweight structure, and existing adopters.

## Decision

Trial an optional human-readable coordination v1 protocol in
`docs/COORDINATION.md`. Extend existing substantial-session records with status,
ownership, scope, acknowledgment, revision pointers, checks, blockers, and next
action using `templates/HANDOFF.md`. Keep existing session headings and naming;
absence of the extension does not invalidate an AI_CONTEXT project.

Add a thin Work startup/return adapter in `examples/CHATGPT_WORK.md`, installed
as `AI_CONTEXT_WORK.md`. Require explicit delivery of the prompt where needed;
do not promise automatic filename discovery, cross-chat visibility, or shared
capabilities. Use reviewed text/patch handoffs when repository writes are absent.

The optional initializer accepts `--coordination` to install instructions and
`docs/HANDOFF_TEMPLATE.md`. Selecting the new `work` adapter includes those files
so its instructions are usable. Existing default output paths and adapter names
are unchanged. Preserve conflict-before-write, dry-run, and explicit force rules.
Do not add surgical updates, automatic messaging, APIs, or runtime dependencies.

All public records use sanitized engineering context. Handoffs never create
new user authorization. Ownership is advisory; branches and human reconciliation
handle concurrent changes rather than pretending Markdown is a lock service.

## Alternatives Considered

- A Work-specific memory directory: rejected because it duplicates shared state
  and makes the core convention depend on one product.
- A task database, service, or mandatory schema: deferred because Git-reviewed
  Markdown is sufficient for the current transfer problem.
- Documentation-only integration: viable manually, but optional packaged support
  makes new-project adoption consistent with existing CLI adapters.
- Mandatory fields added to every existing session: rejected because existing
  projects and simple session records should remain valid without migration.

## Rationale

The repository is the common durable interface, while each session may have
different tools and permissions. Explicit revision/evidence pointers and a
publication/acknowledgment step make transfers inspectable without exposing
private chats. Keeping the extension optional preserves ADRs 0001 and 0002.

## Consequences

- Existing projects can adopt by copying files and adding a conditional adapter
  instruction; the initializer is not an existing-project migration tool.
- Packaged copies need resource synchronization and installed-wheel checks.
- Status and ownership require human/agent maintenance; no automated lock,
  synchronization, validator, or stale-owner recovery is promised.
- Live Work tool permissions and automatic instruction loading remain deployment
  specific and must be checked per session; no live Work trial is claimed here.
- Keep this decision experimental pending PR review and real-project use.

## Supersedes / Superseded By

None. Extends the reference workflow without superseding ADR 0001 or ADR 0002.
