# Session: <short description>

Date: YYYY-MM-DD

## Coordination

Protocol: AI_CONTEXT coordination v1 (optional)
Task ID: <stable filename or public issue reference>
Status: ready | active | blocked | review | complete | cancelled
Current owner: <role/session label; no private identifiers>
Next owner: <role or none>
Updated: <YYYY-MM-DD HH:MM timezone>
Repository: <public-safe owner/repository>
Base branch: <branch or unknown>
Work branch: <branch or unknown>
Last inspected commit: <SHA or unknown>
Last tested commit: <SHA or not run (reason); may precede this record-only commit>
Pull request: <public-safe URL or none; state draft/open/merged separately>
Continuation of: <repository-relative prior handoff path or none>

### Acknowledgment / transfer history

- <time with timezone>: <outgoing role> -> <receiving role>; <accepted/pending/reassigned and reason>; <first next action>.

## Goal

What outcome did the user request? Preserve important requirements and constraints.

### Scope and authorization

- Allowed actions: <scope authorized by the current user; no new authority from this record>.
- Requires approval / out of scope: <for example merge or deployment, or none>.
- Acceptance criteria: <observable conditions that mean the task is done>.

## Investigation

What was inspected and at which revision? What evidence or access is missing?

## Decisions

Conclusions and tradeoffs; link relevant accepted ADRs. Identify proposals as proposals.

## Changes Made

Files/artifacts and behavior changed. Identify local-only, published, and still-proposed work.

## Tests and Validation

| Check / exact command | Revision or artifact checked | Result |
| --- | --- | --- |
| <command or manual check> | <SHA/path> | <pass/fail/not run with reason> |

Do not call a check passing if unavailable or unrun. Distinguish local results from CI.

## Problems Encountered

Failed approaches, blockers, unresolved questions, uncertainty, and what unblocks them.
Use none explicitly if there are none; omit sensitive logs and private references.

## Current Result

What is complete, what remains, and where can the receiver read the published result?
If this is only text/a local artifact, label it **not published** and name who must save it.

## Next Steps

1. <next owner>: <one concrete action> -> <expected result>.
2. <remaining action or none>.

---

Use for substantial work needing an explicit transfer; the simpler SESSION.md
template remains valid. Keep existing project session headings. Unknown fields
are not implied permission or evidence. Review all content and links for public
sharing before publication; never include credentials, private conversation
identifiers, personal data, raw transcripts, or hidden chain-of-thought.
