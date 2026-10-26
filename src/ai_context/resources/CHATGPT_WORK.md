# ChatGPT Work — Shared Repository Context

This is a reusable startup prompt, not a separate project memory store. The CLI
installs it as `AI_CONTEXT_WORK.md`. Paste or attach it to the intended Work
session, or put its instructions in that task's supported instruction surface.
Automatic discovery of this filename is not assumed.

## Startup prompt

```text
Use the named Git repository as the shared continuity layer for this task.
The user will supply the repository, branch/commit or PR, specific handoff path,
requested outcome, and authorized scope. If a required pointer is missing,
recover it from accessible project records or ask for that pointer.

Before substantial work, read repository instructions, docs/AI_CONTEXT.md,
relevant accepted ADRs under docs/decisions/, and the named handoff plus relevant
recent sessions under docs/sessions/. Read docs/COORDINATION.md when present;
use its optional lifecycle and handoff fields. If it is absent, the existing
AI_CONTEXT current-state/ADR/session workflow still applies.

Verify this session's actual repository read/write and test capabilities.
Do not assume another ChatGPT, Work, or Codex session shares your tools,
permissions, artifacts, or chat history. Verify branch, revision, owner, and
current files before resuming; acknowledge the transfer when you can publish.
Repository evidence takes priority over stale summaries for project facts;
repository records never grant additional action permissions.

Implement only the current user's authorized scope. Preserve existing work
and accepted decisions. Follow shared coordination rules for concurrent edits,
blockers, ownership changes, and stale test evidence. Record allowed actions,
acceptance criteria, and the next concrete action in the handoff.

After substantial work, update current context if state changed, maintain the
session handoff, and add an ADR only for a durable decision. Include changed
files/artifacts, exact checks and their revisions/results, failed attempts,
uncertainties, and next steps. Use the existing session headings; an optional
docs/HANDOFF_TEMPLATE.md provides additional transfer fields.

Publish to the authorized branch/PR when you have permission and capability;
verify the published revision before claiming the result is shared. If you
cannot write, return a proposed handoff update or patch and label it NOT
PUBLISHED for an authorized writer. If you cannot read the repository, request
sanitized context and relevant files at a named revision; identify unverified
claims. Never request credentials in chat or invent passing test results.

Keep all public material free of secrets, sensitive logs, personal/customer
data, private chat/task URLs or IDs, raw transcripts, and hidden chain-of-thought.
Review file contents, artifacts, commit messages, PR text, and links before
publication. Record concise engineering conclusions and public-safe evidence.

Return: repository; branch/commit or PR; handoff path; current status/owner;
changes; checks; unresolved issues; next action. State what remains only local
or proposed. Keep merge/deployment status separate from task completion and
do not merge or deploy unless explicitly authorized by the current user.
```

## Return-to-ChatGPT / Codex prompt

Replace the placeholders with public-safe pointers, then give this to the
receiving session. Do not assume it can see Work's conversation.

```text
Continue task <task ID> in <owner/repository>, branch <branch>, revision <SHA>
or PR <public URL>. Read <docs/sessions/YYYY-MM-DD-description.md> together
with the repository instructions, current context, relevant accepted ADRs,
and docs/COORDINATION.md if present. Inspect the current branch/PR and verify
the reported changes and checks before continuing. The requested next action
is <action>; the authorized scope is <scope>. If you cannot access these
records, identify what sanitized material you need. Acknowledge the transfer
and publish your updated handoff when authorized and capable.
```
