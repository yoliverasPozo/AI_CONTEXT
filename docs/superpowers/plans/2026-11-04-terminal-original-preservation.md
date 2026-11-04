# Terminal pagination preservation correction and review gate investigation

Authorized scope: incorporate Codex's PR13 P2 finding into the ongoing pilot
readiness work. Preserve the existing branch/work and original receipts; no live
Project writes, merges, credential expansion or recurring automation changes.

1. Reconcile the live read-only pilot baseline on merged main. Do not invent a
   target if every open PR is already tracked; leave proposal identifiers unset.
2. Reproduce a terminal count change with a missing approved original, followed
   by a synthetic stable snapshot. Cover active and archived originals and prove
   the defect before changing the reader.
3. On a terminal page, require every approved original item ID before permitting
   the typed count-change restart. Keep all existing field/archive/identity and
   malformed-pagination guards, one mutation attempt and durable failure evidence.
4. Run focused and full offline tests and independent review. Preserve historical
   journals byte-for-byte. Reuse the existing stabilization branch for a corrective
   draft PR rather than beginning a parallel implementation.
5. Inspect actual GitHub review/check timestamps and branch rules. Propose a
   current-head review-completion gate with reviewer identity and findings
   disposition; document activation requirements without changing repository
   settings, adding workflows, or requesting reviews through bot commands.

The defect has a precise required behavior; no broader stabilization redesign is
needed. Review completion and finding resolution are separate conditions. A
successful CI check alone cannot attest that both reviewers finished.
