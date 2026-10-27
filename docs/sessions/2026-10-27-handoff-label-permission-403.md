# Session: Debug GitHub inbox label permission failure

Date: 2026-10-27

## Goal

Resolve GitHub Actions `AI_CONTEXT handoff inbox` failures while routing an
opted-in PR to `ai-next:work`, without changing automatic Work/Codex
execution or merging the test PR.

## Investigation

- [Failed workflow run 40571660364](https://github.com/yoliverasPozo/AI_CONTEXT/actions/runs/40571660364), triggered by `pull_request_target` activity on [PR #8](https://github.com/yoliverasPozo/AI_CONTEXT/pull/8), completed with `route` failure.
- Job ID: `122427171562`. The step `Synchronize opt-in agent inbox label` failed with HTTP **403**, `Resource not accessible by integration`, while calling `POST /repos/yoliverasPozo/AI_CONTEXT/issues/8/labels`.
- GitHub runner reported effective `GITHUB_TOKEN` permissions: `Issues: write`, `PullRequests: read`, `Contents: read`.
- The marker `<!-- ai-context-next: work -->` is present in PR #8's description, and the label remained absent. The event handler ran, so this is not an event-subscription problem.
- GitHub's REST label endpoint documents `Issues: write` OR `Pull requests: write` as suitable fine-grained permissions. Because `Issues: write` was already reported but the PR label operation was rejected, `Pull requests: write` is the smallest additional permission worth testing. This is an evidence-based hypothesis, **not** a proven complete remedy.

## Decisions

- In `.github/workflows/agent-handoff-inbox.yml`, increase only
  `pull-requests` from `read` to `write` for the opt-in label router.
- Retain `issues: write` for label creation and `contents: read`.
- Retain same-repository PR guard, no checkout or PR-code execution,
  literal marker parsing, managed-label-only API calls and no auto-merge.
- Do not introduce PATs, GitHub App secrets or broader organization changes.
- The workflow needs to reach the default branch before the next live
  `pull_request_target` run uses the changed permissions.

## Changes Made

- Applied the minimal workflow permission change in branch
  `fix/handoff-inbox-pr-label-write-permission`.

## Tests and Validation

- Read actual failed `route` job logs through the connected GitHub
  Actions API; confirmed HTTP status, URL and effective permissions.
- Fetched existing workflow and verified the expected permissions block
  before applying the modification.
- `pull_request_target` live event / PR #8 label recheck: **not tested**
  with the new workflow because it is still in a feature branch.
- Ordinary repository CI on the fix PR should be checked separately;
  passing Python tests will not establish label API write permission.

## Problems Encountered

The GitHub API can deny a PR label request even with an apparently suitable
listed token permission. If adding `pull-requests: write` does not resolve
the error, inspect the new `route` log and effective token policy; do not
assume a permission fix works without a live rerun.

## Current Result

A proposed minimal permissions fix is committed on a separate branch.
No existing PR has been merged or modified by this proposal.

## Next Steps

1. Review the workflow diff and approve/merge the fix PR separately if acceptable.
2. After merging the fix into `main`, generate a fresh description edit on
   existing [PR #8](https://github.com/yoliverasPozo/AI_CONTEXT/pull/8).
   Confirm the latest `route` run succeeds and `ai-next:work` appears.
3. Confirm that the Work watcher handles the PR event without duplicate
   execution or unauthorized write. Keep other projects out of scope.
