# Diagnostic coverage and bounded verification stabilization

Authorized scope: review PR Lens findings on PR12 and add a configurable,
read-only post-add stabilization mechanism. No live Project calls/writes, schedules,
credentials or original receipt writes during implementation. Original operation
inventories are checked before/after in the private coordination workspace.

Design decisions:

- Audit every static validation error in writer_github and map it to a fixed code;
  unknown runtime exceptions remain unknown and stop. Tests trigger representative
  missing-message failures through real reader/value boundaries.
- Optional `verification` config: max_attempts1..5 (default1), max_seconds1..120
  (default30), max_calls1..30 (default10). More than1 attempt requires rate_floor
  at least200. Existing lifetime reader caps/floor also apply.
- Only after a new acknowledged add, restart a complete read from cursor=None for
  exactly pagination_count_changed. A failed attempt is durably recorded before
  any next attempt. Never combine pages across attempts.
- Check already-observed original items/fields, exact scope/head and acknowledged
  target identity/archive state during every attempt, before allowing a count
  restart. Stop on genuine drift, unknown errors, rate/call/time exhaustion.
- Monotonic deadline bounds each gh read timeout and acceptance; all attempts share
  API call counters; page cap applies per attempt. No read restart in
  prepare/preflight/recover or on old spent intents.
- Preserve per-attempt sanitized evidence and one final receipt. Successful
  stabilization during this live invocation may complete; historical needs_review
  is never promoted or replayed. Mutation transport remains one attempt only.

Tasks: RED diagnostic tests, mapping/audit; RED paginated synthetic tests,
implementation; full suite and independent review; docs/context/ADR + private
historical consistency analysis; draft PR/natural CI with exact-head evidence.
