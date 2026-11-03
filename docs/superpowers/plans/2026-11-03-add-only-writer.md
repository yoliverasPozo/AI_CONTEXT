# Add-only writer implementation plan

> Execute inline with superpowers:executing-plans; independent whole-branch review.

**Goal:** Disabled single-PR addition with durable receipts and no other remote mutation.
**Architecture:** Separate reader/transport, pure state policy, journal and CLI.
**Tech Stack:** Python 3.10+, standard library, existing gh authentication.
**Spec:** [design](../specs/2026-11-03-add-only-writer-design.md).

## Global constraints

No real mutation, credential grants, schedule or routing changes in this task.
No installed core or planner behavior changes. Public fixtures use generic IDs.
One mutation attempt per operation; recovery and rollback assessment only read.

## Review focus

- Wrong head/Project or a changed original field must prevent the mutation.
- Lost response or restart after durable intent must never resend the add.
- Concurrent/preexisting target must not grant deletion ownership.
- Receipt failure/corruption or concurrent local process must stop mutation.
- Unreadable, truncated or unsupported populated data must not validate preservation.

## Tasks

- [x] Policy + receipts (`writer.py`, `writer_journal.py`, `tests/test_project_writer.py`):
  RED tests for one-item scope, strict state comparisons, no-op archives, approval,
  one attempt, recovery and rollback proposals; implement then full suite.
- [x] Live adapter (`writer_github.py`, `tests/test_project_writer_github.py`): RED controlled GraphQL tests
  for complete pagination, type support, identity, rate guards and the sole fixed
  mutation; implement with subprocess output sanitization; full suite.
- [x] CLI (`writer_cli.py`, generic disabled example): RED command tests for
  disabled execution, prepare/recover output and no accidental mutation; implement;
  full suite. Local-only live prepare may verify reader schema without execution.
- [x] Documentation/ADR/session/current context, independent review, regression
  fixes, privacy/link/whitespace verification, draft PR and natural CI. Private
  The private pilot plan contains real IDs/head/digest and is never public.

Evidence: 85 tests pass locally and independently; see
[review](../../reviews/2026-11-03-add-only-writer.md). Delivery/CI evidence belongs
in the draft PR. No mutation, credential, schedule or routing path was activated.
