# Session: Pull request readiness policy

Date: 2026-11-05

## User Goal

Default completed, validated work to Ready for Review for Codex and ChatGPT
Work. Keep merge authority separate and apply the policy prospectively.

## Investigation

The shared coordination guide, repository instructions, and installed Codex
and Work prompts are the relevant instruction surfaces. The optional handoff
template already records PR state. The initializer packages copies of the
reference instructions and template.

## Decisions

Document Ready for Review as the default when publication is authorized.
Require current-head CI and automated review evidence before reporting merge
readiness. Preserve explicit Draft requirements, existing handoff statuses,
and owner approval for protected actions.

## Changes Made

Updated the coordination guide, repository and agent instructions, and the
optional PR status placeholder. Synchronized their packaged copies.

## Tests

All 118 existing tests passed, including checks for resource parity and
installation of the optional coordination and Work instructions.

## Problems Encountered

The handoff status `ready` and GitHub's Ready for Review serve different
purposes. The policy records GitHub review state separately from handoff status.

## Current Result

Status: review

Current owner: Codex implementer

Work branch: `docs/pr-review-readiness`

## Next Steps

Review the policy change on the published revision. Verify required CI and
automated review evidence before requesting a separate merge decision.
