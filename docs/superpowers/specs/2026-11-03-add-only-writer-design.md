# Disabled single-item add-only writer

## Intent and constraints

Extend the separately tested read-only Project adapter with an optional,
source-only, Python-standard-library writer. The installed initializer, planner,
agent routing, repository labels, fields and schedules retain their contracts.
The owner requested implementation and a draft PR, not live mutation permission.
All implementation tests use controlled transports. Real account identifiers,
portfolio snapshots and pilot authorization records stay outside this public repo.

## Approaches

1. Apply the existing planner's whole result: rejected. It includes field and
   notification proposals, exceeds a single-item pilot and increases recovery scope.
2. One approved content identity per operation, strict state rechecks and a
   durable attempt journal: selected. Smallest useful mutation surface.
3. Automatic transactional rollback: rejected. GitHub's add returns an existing
   item ID when already present and does not provide a created-by-this-call flag
   or compare-and-swap. An uncertain response cannot prove deletion ownership.

## Operation contract

- Separate source-only CLI. `prepare` reads and writes a local private proposal;
  `apply` requires both `--execute` and a config with `enabled: true`, plus an
  owner-approved exact proposal SHA-256 and expiration. Default config is disabled.
  The record captures scope, not proof of human consent; actual owner authority
  remains external. No login or permission setup is implemented.
- One Project ID and one open same-owner PR node/repository/number/head. No
  bulk apply, draft issues, field changes, archive changes, deletes, routing,
  notifications, deployment, workflow or schedule mutation.
- `prepare` requires an exact Project owner/type/number/ID match, complete
  archived and unarchived membership, readable field definitions/values and a
  current open PR at the expected SHA. Unsupported populated field types,
  missing/redacted identities, duplicate IDs, truncation and low rate budget
  refuse preparation. All current supported scalar/identity values are compared;
  unsupported types fail closed rather than disappear from a fingerprint.
- The proposal contains canonical complete before state, target identity, schema
  version, operation ID, creation/expiration times and exact-state digest.
  No credentials, PR body or handoff prose is in the receipt.
- `apply` first validates enablement, approval digest/operation/expiration,
  strict proposal schema, local receipt destination and one-use attempt ledger.
  It re-reads all Project fields/items and PR identity/head. Any expected-state
  drift aborts before mutation. Existing target, including archived membership,
  is a no-op and never unarchives or edits the item.
- Immediately before the sole mutation, persist/fsync an append-only intent
  event. The mutation is exactly `addProjectV2ItemById`; no generic caller-supplied
  GraphQL document is accepted. No automatic mutation retries.
- Persist response identity before post-read where possible. Read back complete
  Project state and PR state; require original items/values/definitions unchanged
  and exactly the target item added, without changing any new-item fields.
  Native Project workflows may populate new-item defaults; capture those values,
  never compensate by writing fields. Drift or unreadable after state is an
  explicit needs-review result, never silent success or automatic reversal.

## Durable recovery and concurrency

One local operation directory created exclusively stores a hash-chained JSONL
journal. Each event is flushed/fsynced. A process lock prevents concurrent use
of that operation; lock recovery is explicit/manual. A durable mutation intent
is permanently spent even if the process dies before it is known whether the
request was sent. Reusing or copying another approval directory is outside the
single-controller coordination contract; global exactly-once is not promised.

`recover` is read-only and never retries the mutation. It checks journal integrity,
then reconciles absent/present/duplicate target, original state and known response
ID. After timeout, present does not mean this process created it, and absent
does not prove a late server commit is impossible. Uncertain ownership stays
unknown. Local journal corruption or write failure stops further mutations.

GitHub has no atomic CAS between pre-read and add. Use one approved pilot
operator, stop other Project writers during the pilot, and treat detected
concurrent state changes as needs-review. Never claim atomic preservation of
unrelated concurrent edits or restore them over a human's changes.

## Rollback

No automatic delete transport or executable rollback command ships. A read-only
rollback assessment compares the receipt with current complete state and can
propose manual removal of only the exact added item when all original items are
intact, target identity matches, response/readback agree and the added item is
unchanged. Existing/no-op, ambiguous/uncertain, missing, archived, modified or
replaced items refuse the proposal. Even an eligible proposal is not ownership
proof and requires a separate operator decision and authorization. Tests exercise
both the valid bounded proposal and preservation/refusal cases.

## Acceptance and delivery

Tests prove disabled default, exact scope/head/state/expiration checks, complete
pagination/archives, duplicate and concurrent-add handling, one mutation attempt,
timeout/crash/recovery, journal failures/integrity, before/after preservation,
rollback refusal and CLI behavior. Independent review and natural exact-head CI
precede a draft PR handoff; no live mutation is invoked. A separate private
authorization plan binds a later one-item pilot to a current source/head, the
exact Project/content ID, proposal digest, maximum one attempt and stop rules.

Sources: [GitHub Projects API guide](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects),
[current Projects schema](https://docs.github.com/en/graphql/reference/projects).
