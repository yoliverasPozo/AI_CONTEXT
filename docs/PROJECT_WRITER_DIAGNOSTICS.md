# Readback diagnostics and supervised pilot acceptance

An acknowledged add can finish with `needs_review` when immediate readback fails.
The operation stays spent; diagnostics and recovery never resend a mutation or
promote an uncertain receipt to complete. A prior pilot lost the immediate
exception/state. Later confirmed membership does not identify its failed predicate;
new diagnostics cannot repair or reconstruct those historical receipts.

## Additive receipt fields

- `diagnostic.phase`: `readback`, `normalize` or `verify_addition`.
- `diagnostic.code`: fixed allowlisted target, preservation, pagination, field,
  access, transport, GraphQL or budget classification. Unknown exceptions become
  `unexpected_error`. Exact codes are in `writer_diagnostics.py`.
- `diagnostic.read_evidence`: per-read times, cumulative read calls/returned points,
  configured limits and at most100 page entries. Pages contain node/total counts,
  next-page flag, cost/remaining and hashes of selected raw item/field/target data.
  No cursor or response body is retained; these are not canonical state hashes.
- `data.observed` in the private journal only, when a complete normalized after
  state exists. Failed/partial reads never become complete acceptance evidence.

No exception message, repr, class name, traceback, subprocess output, credential,
endpoint, arbitrary backend key or raw GraphQL error is serialized. Internal static
validation messages map to fixed codes without echoing text. The CLI shows metadata;
complete values stay in private journals under existing before/after privacy rules.

Old receipts remain readable. Acceptance predicates, approval/enablement, expiry,
spent intent, no-op and rollback rules are intact. Diagnostic persistence failure
leaves intent spent. No read/mutation retries, compensation, credentials, schedules
or new apply pathway are introduced.

## Why the historical trigger remains unknown

Two synthetic generic45-item, three-page tests both yield one acknowledgment,
six total reads,120 returned points and later successful read-only recovery:

1. Complete prior membership without the acknowledged item: `target_absent`, with
   complete observed state retained.
2. New item with an unreadable repository relation on the final page:
   `unreadable_field_relation`, page evidence retained, no complete observed state.

These counterexamples prove aggregate-trace ambiguity, not either historical cause.
Native defaults on the new item are already permitted. Their presence alone does
not explain failure; original-item, definition and identity drift still stops.

## Measurable second-pilot criteria

Prerequisites: exact diagnostic source reviewed/approved, local suite and four
existing Windows/Linux Python CI jobs green; existing auth reverified without
scope expansion; restricted local storage; complete archives/field reads; one
operator/quiet window. Use a separately approved absent target and a new900-second
proposal with explicit source/Project/content/digest/expiry/one-attempt authority.
Never remove/re-add an existing pilot target or reuse/rebuild its operation.

A clean pass requires:

- One mutation attempt, zero retries; valid digest/head/expiry at preflight and
  after intent fsync. A refusal before send has zero attempts.
- Exactly one expected item, count+1, matching acknowledgment/readback identity,
  identical original IDs, archive flags, definitions/options and populated values.
- Native defaults captured only on the new item. No explicit field, routing,
  credential, schedule, notification or production mutation introduced.
- One `complete` receipt, full before/after, independently matching membership,
  disabled one-shot config and verified journal/receipt hashes.
- Approved call/page bounds and remaining-point floor satisfied on every recorded
  response (reference floor200). Actual read points reported separately from
  unmeasured mutation cost; shared bucket differences are not usage attribution.

On failure stop. A diagnosable safety stop has a known non-generic code, phase,
bounded evidence locating the failed condition and normalized state if available.
Recover only with reads; later presence never converts needs_review into a clean
pass. Unknown errors, missing evidence, unexplained drift or receipt failure block
wider acceptance. Containment is not unattended-operation acceptance.

Mutation controls can contain a supervised failure, but use the reviewed diagnostic
revision before another write pilot. Historical cause remains unknown. Recurring
or unattended activation requires separate acceptance and owner authorization.
