# Writer readback diagnostics plan

Scope authorized by the anomaly investigation request: preserve sanitized error
classifications and focused evidence without changing any acceptance predicate,
retry, credential, scope, enablement or mutation behavior. Original pilot receipts
are read-only evidence, never inputs to apply/recover during this investigation.

Design: append a fixed-code diagnostic to new needs_review receipts and CLI
results; record stage, bounded counts/budgets/page fingerprints and complete
normalized observed state when available. Never serialize exception text, repr,
tracebacks, transport bodies, credentials or arbitrary backend diagnostic keys.
Unknown exceptions become unexpected_error. No automatic read or write retry.

Tasks:

1. Reconstruct original journal/CLI/metadata, verify hashes, and enumerate which
   post-acknowledgment predicates remain possible. Do not infer a lost snapshot.
2. RED tests for post-read failure classification, exact addition-check failures,
   snapshot retention, pagination/rate evidence, sanitization and spent replay;
   implement minimal diagnostics in writer/reader, keeping collector unchanged.
3. Run the full suite, independent review and focused regressions; update guide,
   experimental ADR0006 and context/session with limits and measurable next-pilot
   acceptance. Publish a reviewable draft PR with natural CI evidence.

Only generic fixtures/public analysis are committed. Private analysis and receipt
hash comparisons stay in the local coordination workspace. Publishing a PR may
trigger existing native intake; no Project API mutation is invoked by this task.
