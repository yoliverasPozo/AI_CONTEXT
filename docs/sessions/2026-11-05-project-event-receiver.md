# Session: Prepare read-only Project event delivery

Date: 2026-11-05

## User Goal

Find a low-cost path from a real GitHub PR event to a read-only reconciliation
controller. Prepare a supervised test with no activation or Project writes.

## Investigation

The prior replay proved GitHub event detection and on-demand recovery. The
saved Work watcher report showed a PR-open event in its cloud task. The
accessible Scheduled view did not expose the saved watcher, and the published
product contract does not establish access from that watcher to the local
controller and ledger. Existing CI records PR-triggered runs without
notifying this controller.

## Decisions

Prepare a bounded loopback receiver for a signed repository webhook. Use an
owner-approved HTTPS ingress for any future live window. Each eligible hint
receives one targeted archive-aware GitHub query. The existing planner handles
complete recovery when delivery is missing or uncertain. A hosted receiver
and a new Actions job are deferred.

## Changes Made

Added an opt-in event receiver, focused tests and a supervised operating
guide. SQLite commits successful delivery and observation in one transaction.
The receiver suppresses exact duplicates across restart, rejects mismatched
ID and body reuse and uses fresh lifecycle and membership for stale events.
A bounded ledger accounts for handled read failures without consuming the
delivery ID.

## Tests

Loopback HTTP, subprocess restart, stale lifecycle, archived membership,
malformed or unsigned requests, ambiguous state and failed-read budget tests
passed. A targeted live query verified the historical open PR and its current
membership. The unchanged planner completed a live 16-repository catch-up
with the event omitted and reported zero missing open PRs.

## Problems Encountered

Independent review reproduced a conflict where a known body under a new ID
could receive success without an immutable binding. The receiver now refuses
the mismatch. The serial loopback server also requires a bounded ingress
deadline and monitored redelivery for the supervised window.

## Current Result

Reviewable local source. No live hook, workflow, status, approval artifact
or Project mutation. The five existing native intake rules remain enabled.

## Next Steps

Review the source and authorize any PR publication with awareness of native
intake. Identify an existing approved non-production HTTPS route and separately
authorize one temporary repository hook, its signing secret and a bounded
window for the next natural PR opening. Verify the GitHub delivery and
committed receipt, then stop and preserve the evidence.
