# Experimental single-item Project writer

This source-only extension adds one approved open PR to a **user-owned** Project.
It is disabled by default and has no workflow, schedule or installed CLI entry
point. The [original planner](PROJECT_SYNC.md) still prints proposals only.
Implementation follows [ADR 0006](decisions/0006-disabled-add-only-project-writer.md).

## Scope and gates

The sole remote mutation is a fixed `addProjectV2ItemById`. There is no field
update, delete, archive, notification, agent invocation, label or routing path.
All original Project item IDs, archive flags, field definitions/options and
populated supported field values must match the approved before state. The
reader explicitly requests both archived and unarchived items. Unknown field
types, redacted items, truncated nested connections and pagination errors stop
the operation. Organization Projects and cross-owner PRs are unsupported.

Execution requires all of the following:

- Local config explicitly has `enabled: true` (the example has `false`).
- Operator supplies `apply --execute` and a separately authorized approval file.
- Approval matches the exact operation, Project/content IDs and proposal digest.
- Proposal and approval are current, expire within one hour, and remain current
  immediately before and after persisting intent.
- The original, exclusively created operation directory has a valid journal and
  no previous intent, completion or no-op. Its lock must be available.
- A fresh complete read matches the proposal's Project/PR identities, exact head
  and original fields/items. A concurrently present target becomes a no-op,
  including archived targets; it is never re-added or unarchived.

An approval JSON is a local scope record, **not authentication of human consent**.
Never generate it as a substitute for owner authorization. Use existing GitHub
CLI authentication; this code has no login, token or scope-expansion command.
Read access does not demonstrate write access. A write denial is an uncertain
attempt requiring read-only reconciliation, not a reason to request more scopes.

## Local operator flow

Run from the repository root with Python 3.10+ and an existing `gh` login. Store
config, receipts and approvals **outside** this public repository, in a private
local directory with owner-controlled permissions. Avoid cloud-synchronized
operation directories for an eventual live pilot. Never commit a live snapshot.
Copy the generic [disabled config](../examples/project_sync/writer_config.example.json)
and replace the placeholder selection privately.

```powershell
python -m examples.project_sync.writer_cli prepare --config C:/private/config.json --operation pilot-one --directory C:/private/pilot-one
```

`prepare` only reads GitHub and creates a new local operation directory containing
`journal.jsonl`. It prints `prepared_unapproved`, SHA-256, expiry, item/archive
counts and API usage. `--snapshot C:/private/snapshot.json` instead uses a complete
offline snapshot; tests demonstrate that path without network access. Existing
operation directories are never overwritten. The proposal is the first event's
`data.proposal`, including full canonical before state.

After owner review of the exact source revision, before state, digest, expiry,
expected target and stop rules, a separately authorized approval file has exactly:

```json
{
  "action": "add_one",
  "operation_id": "pilot-one",
  "proposal_sha256": "<exact prepared digest>",
  "project_id": "<exact Project node ID>",
  "content_id": "<exact PR node ID>",
  "expires_at": 2000000000
}
```

The timestamp is an illustrative Unix time, not a valid approval. Its expiration
must not exceed the prepared proposal's expiry. Only after authorization may an
operator set the private config to `enabled: true` and invoke:

```powershell
python -m examples.project_sync.writer_cli apply --config C:/private/config.json --directory C:/private/pilot-one --approval C:/private/approval.json --execute
```

One fsynced intent precedes at most one mutation attempt. The mutation is never retried.
A complete receipt stores the response item ID and full after state. All original
items/values must remain equal and exactly the target may be added. New-item
defaults populated by existing native Project workflows are captured, never
overwritten. Existing native automations/subscribers may react to membership;
absence of an explicit notification API is not a promise of no native effects.

## Failure recovery and rollback assessment

Exit 0 means prepared, an already-present no-op, verified presence, or a successful
manual rollback assessment; inspect `status`/`action` to distinguish them. Exit 2
means refusal/input/read/receipt error. Exit 3 means uncertain, needs-review or
read-only reconciliation requiring an operator decision. After any attempted
mutation or local receipt failure, preserve the directory and use only reads:

```powershell
python -m examples.project_sync.writer_cli recover --config C:/private/config.json --directory C:/private/pilot-one
python -m examples.project_sync.writer_cli rollback-assess --config C:/private/config.json --directory C:/private/pilot-one
```

Recovery persists the observed complete state in the local journal, but never
sends an add. An intent remains spent even after a crash before transmission.
New `needs_review` receipts preserve a sanitized classification, verification
phase and bounded page/rate evidence, plus normalized observed state when available.
See [diagnostics and next-pilot criteria](PROJECT_WRITER_DIAGNOSTICS.md). Old
receipts remain readable; lost observations cannot be reconstructed. Diagnostic
capture does not change acceptance or retry behavior.
Replaying a completed or no-op operation returns its stored historical result;
it does not perform a fresh verification or regain permission to send.
An absent item cannot exclude a late commit; a present item cannot prove who
created it. A leftover lock or truncated/corrupt receipt requires manual
investigation, never automatic clearing, rebuilding, copying or resending.
Receipt hashes detect accidental changes; they do not authenticate an author or
protect against an actor able to rewrite the whole journal. Filesystem fsync is
best-effort host durability, not a guarantee against storage loss or rollback.

GitHub's add can return an existing item ID. It has no creation-ownership flag,
transaction across read/add, or compare-and-swap guard. Thus even successful
readback says `ownership: not_proven`. Only a complete unchanged receipt can
produce a **non-executable manual removal proposal**. Preexisting/no-op, uncertain,
modified, archived, replaced or otherwise changed states refuse assessment.
Any actual removal requires a separate owner decision and authorization.

Use one operator and one original operation directory per approved pilot; stop
other writers for the window. The lock is local to that directory, not a global
Project lock. Copying/rebuilding journals or approvals defeats local attempt
tracking. Concurrent changes after a read can occur; detected changes cause
`needs_review` and are preserved, never overwritten to manufacture success.

The read budget and remaining-point floor are explicit config limits. Reported
read points sum response `rateLimit.cost`; mutation attempts count sends, not
measured GraphQL cost. Rate counters are shared with other clients. Bounds may
stop after-state reads following a successful add; this is `needs_review`, with
read-only recovery required. No recurring deployment is included or approved.

## Optional post-add read stabilization

An optional policy can be reviewed with the fresh source/config/proposal:

```json
"verification": {"max_attempts": 3, "max_seconds": 30, "max_calls": 9}
```

Defaults are1 attempt,30 seconds,10 verification calls; hard caps5/120/30. More
than1 attempt requires rate_floor>=200. Existing lifetime call cap, per-attempt
page cap and per-response rate floor remain in force. Only the internal pagination_count_changed guard can restart after a new
acknowledgment. Every restart begins at page1 and discards prior partial pages.
Item shape, explicit archive state, fields, original values, exact identity and
cursor validity are checked before retry eligibility. Every failed attempt is
journaled before another read. Unknown errors, genuine drift, evidence-write or
budget failures stop. Transport timeout uses remaining monotonic time, checked
through final validation before acceptance; final receipt fsync is not interruptible.

A terminal page must also contain every approved original item ID, including
archived originals, before a count mismatch can permit a restart. A terminal
omission stops with `original_item_changed`; a later stable read must not conceal
that observed omission. Invalid counts and incomplete pages remain fatal even
when another page reported a different count.

Prepare, preflight and recover remain single-read paths. Changing config cannot
replay a spent intent or promote historical needs_review. No mutation resend,
compensation, credential, schedule or routing path is introduced. See
[ADR0007](decisions/0007-bounded-post-add-readback.md) and
[message coverage audit](reviews/2026-11-04-reader-error-coverage.md).

Sources: [GitHub Projects API guide](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects),
[Projects schema](https://docs.github.com/en/graphql/reference/projects).
