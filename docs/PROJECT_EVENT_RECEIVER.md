# Read-only Project event receiver pilot

The source-only receiver records one repository's GitHub pull request events.
It binds to loopback and exits after the selected test window. The existing
[planner](PROJECT_SYNC.md) still performs complete catch-up. The receiver
has no Project writer integration.

## Delivery options

- A managed ChatGPT GitHub event task can receive eligible PR activity without
  Actions compute. Account access and delivery to a specific controller must
  be verified separately. Web tasks do not directly share the Windows
  controller's files or SQLite ledger.
  [Scheduled tasks](https://learn.chatgpt.com/docs/automations#trigger-tasks-from-app-events)
- Actions run metadata can corroborate a PR event. Reading a run is an
  on-demand recovery option. A metadata-only workflow would still need an
  approved transport to notify a separate controller. A single short job
  consumes at least one rounded minute of standard private-repository runner
  usage. [Actions events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
  · [Runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing)
- The pilot can use a GitHub repository webhook on an approved HTTPS ingress.
  GitHub pushes the event without using Actions minutes. Keep the HTTPS
  route and loopback receiver reachable during the supervised window. A
  webhook subscription alone cannot reach a controller behind a firewall.
  [Repository webhooks](https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks)

## Receiver behavior

The ingress forwards the original request body and GitHub event, delivery,
and signature headers to `127.0.0.1:8765/github/pr`. Keep TLS verification on.
Forward only POST on this path, buffer the complete request, reject bodies over
256 KiB, disable body logging and retries, and enforce request deadlines and
rate limits before forwarding. Scope ingress separately from production routes.
The prototype uses a serial Python loopback HTTP server. Validate the entire
response path against GitHub's ten-second timeout in the approved test window.

The receiver verifies HMAC-SHA256 before decoding the body. It checks the
configured repository ID and PR hint, then reads that exact PR's current
database ID, node, head and lifecycle and its membership in the selected private
user Project. The single query includes archived items and stops if the
connection is incomplete, the identity is ambiguous or the rate floor of 200
is breached. The query's subprocess timeout is four seconds. Only
`opened`, `synchronize`, `reopened` and `closed` are evaluated. A signed
repository ping confirms reachability. An older event always uses fresh state.

A private SQLite file stores the delivery ID, payload digest and a receipt in
one transaction before an HTTP 200 acknowledgment. It suppresses exact
redeliveries, rejects mismatched ID/body reuse and distinguishes changed
observations from unchanged state. The ledger stores fixed metadata and
does not keep the raw event, PR text, signature, or credentials. The ledger
caps targeted reads at 20 committed attempts, including handled failures.
An interruption before SQLite commits can leave a read uncounted, with no
successful acknowledgment. Use one ledger and one receiver for the
test. Keep the ledger on local, owner-controlled storage outside the repo and
cloud sync. Protect the database and SQLite journal with the parent directory
permissions. Supply the separate webhook secret through the process environment
as `AI_CONTEXT_WEBHOOK_SECRET`. Use a randomly generated secret with at least
32 bytes of entropy and keep it out of source, logs and shell history.
[Signature validation](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)

## Supervised test and recovery

1. Record the reviewed receiver SHA, exact repository and Project IDs, operator
   and UTC start/end. Read current inventory with the existing authenticated
   CLI and validate the TLS route and restricted ledger directory. For this
   one-repository test, GitHub repository admin access is needed only to install
   or remove the webhook. The receiver needs existing PR and Project read
   access. Keep its CLI login on the trusted host.
2. With separate owner authorization, start
   `python -m examples.project_sync.event_receiver --repository OWNER/REPO --repository-id ID --project-id NODE --ledger ABSOLUTE_PATH --port 8765 --seconds 1800`.
   Register one repository webhook for pull requests, with JSON content and
   the approved HTTPS destination and secret. Verify the signed ping.
3. Wait for the next legitimate PR opening. Compare the GitHub delivery ID
   and response with the local ledger receipt and independently read the PR
   head, lifecycle and archive-aware membership. If the PR is absent, record
   that observation and keep it read-only. Accept a test pass only when
   automatic delivery and a committed receipt both exist.
4. During the same approved window, restart with the same ledger and request
   one GitHub redelivery of that delivery. Confirm one receipt for the delivery
   and the same membership observation. Stop the receiver and remove the
   approved webhook and temporary route at the end of the window. Preserve
   the ledger and release the temporary secret.
5. On timeout or failed delivery, inspect GitHub's delivery log and the local
   ledger before an operator-authorized redelivery. GitHub does not redeliver
   failed webhooks automatically. When the receiver was offline, evidence
   is incomplete, or no valid association can be made, run
   `python -m examples.project_sync --config PRIVATE_CONFIG --live`.
   Compare the complete result against the last accepted observation. It
   recovers current membership and lifecycle, while transitions that happened
   and reversed between reads may be unknowable.
   [Redelivery](https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/redelivering-webhooks)

No workflow or service is installed by this example. The test window needs a
reachable receiver only while observing live events. Recurring operation would
need an independently validated ingress, durable handling of queued deliveries
and a separate owner decision.
