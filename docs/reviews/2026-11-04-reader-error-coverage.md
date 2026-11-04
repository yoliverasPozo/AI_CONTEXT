# Static reader error coverage audit

Both overlapping PR Lens findings on [PR12](https://github.com/yoliverasPozo/AI_CONTEXT/pull/12#issuecomment-6637865830) reproduce.
Audit: 78 literal guard locations in writer_github and invoked normalization/
collector helpers, zero unmapped messages. Focused tests trigger relation, identity,
unavailable-node, collection and configuration failures through real boundaries.
Unknown runtime errors remain unexpected_error; matching text cannot enable retry.
This static coverage snapshot does not classify every arbitrary malformed payload.

| Source | Static validation message | Sanitized code |
| --- | --- | --- |
| collector.py:27 | `GraphQL response exceeds 16 MiB limit` | `response_bound_exceeded` |
| collector.py:41 | `only read queries are supported` | `query_scope_invalid` |
| collector.py:43 | `GraphQL call budget exhausted` | `call_budget_exhausted` |
| collector.py:54 | `GraphQL returned errors; no partial plan produced` | `graphql_error` |
| collector.py:57 | `GraphQL data missing` | `response_shape_invalid` |
| collector.py:59 | `GraphQL rate-limit evidence missing` | `rate_evidence_missing` |
| collector.py:63 | `GraphQL rate floor reached; collection stopped` | `rate_floor_reached` |
| collector.py:68 | `missing or malformed collection page` | `page_shape_invalid` |
| collector.py:72 | `pagination evidence missing` | `pagination_invalid` |
| collector.py:74 | `next-page cursor missing` | `pagination_invalid` |
| collector.py:76 | `collection contains unreadable node` | `unreadable_node` |
| collector.py:82 | `nested collection truncated; no partial plan produced` | `nested_collection_incomplete` |
| writer.py:25 | `complete writer snapshot required` | `snapshot_incomplete` |
| writer.py:29 | `invalid Project selection` | `snapshot_scope_invalid` |
| writer.py:31 | `invalid or closed Project` | `snapshot_scope_invalid` |
| writer.py:34 | `invalid single PR target` | `snapshot_target_invalid` |
| writer.py:36 | `PR target must be same-owner, open and exact-head` | `snapshot_target_invalid` |
| writer.py:42 | `invalid field definitions` | `field_definitions_invalid` |
| writer.py:44 | `invalid field identity` | `field_definitions_invalid` |
| writer.py:47 | `duplicate field definition` | `field_definitions_invalid` |
| writer.py:51 | `snapshot exceeds receipt bound` | `snapshot_bound_exceeded` |
| writer.py:53 | `non-JSON or non-finite field value` | `invalid_item_fields` |
| writer.py:59 | `item bound exceeded` | `snapshot_bound_exceeded` |
| writer.py:62 | `invalid or redacted Project item` | `invalid_item` |
| writer.py:66 | `duplicate item/content identity` | `duplicate_identity` |
| writer.py:68 | `invalid item fields` | `invalid_item_fields` |
| writer.py:71 | `unsupported or duplicate populated field` | `invalid_item_fields` |
| writer.py:79 | `snapshot exceeds receipt bound` | `snapshot_bound_exceeded` |
| writer.py:81 | `non-JSON or non-finite field value` | `invalid_item_fields` |
| writer_github.py:61 | `invalid writer config` | `invalid_configuration` |
| writer_github.py:62 | `enabled must be an explicit boolean` | `invalid_configuration` |
| writer_github.py:64 | `invalid Project scope` | `invalid_configuration` |
| writer_github.py:65 | `this pilot writer supports user-owned Projects only` | `invalid_configuration` |
| writer_github.py:66 | `invalid target scope` | `invalid_configuration` |
| writer_github.py:69 | `invalid read limits` | `invalid_configuration` |
| writer_github.py:71 | `unsafe read limit` | `invalid_configuration` |
| writer_github.py:73 | `invalid verification limits` | `invalid_configuration` |
| writer_github.py:75 | `unsafe verification limit` | `invalid_configuration` |
| writer_github.py:76 | `stabilization requires rate floor at least 200` | `invalid_configuration` |
| writer_github.py:81 | `unreadable field value` | `unreadable_field_value` |
| writer_github.py:84 | `unknown populated field value` | `unsupported_field_value` |
| writer_github.py:92 | `missing populated collection` | `field_collection_incomplete` |
| writer_github.py:94 | `unreadable field relation` | `unreadable_field_relation` |
| writer_github.py:95 | `duplicate field relation` | `duplicate_field_relation` |
| writer_github.py:98 | `unsupported or incomplete populated field` | `unsupported_field_value` |
| writer_github.py:102 | `redacted or malformed populated relation` | `unreadable_field_relation` |
| writer_github.py:104 | `repository relation unreadable` | `unreadable_field_relation` |
| writer_github.py:106 | `milestone relation unreadable` | `unreadable_field_relation` |
| writer_github.py:108 | `field identity unavailable` | `field_identity_unavailable` |
| writer_github.py:136 | `verification elapsed budget exhausted` | `verification_time_exhausted` |
| writer_github.py:141 | `verification call budget exhausted` | `verification_call_budget_exhausted` |
| writer_github.py:151 | `original item/field state changed` | `original_item_changed` |
| writer_github.py:153 | `unrelated Project membership changed` | `unexpected_membership` |
| writer_github.py:154 | `target response item differs` | `target_item_mismatch` |
| writer_github.py:155 | `target archived after acknowledgment` | `target_archived` |
| writer_github.py:170 | `verification evidence persistence failed` | `verification_receipt_failed` |
| writer_github.py:199 | `verification elapsed budget exhausted` | `verification_time_exhausted` |
| writer_github.py:258 | `Project/PR unavailable` | `project_or_pr_unavailable` |
| writer_github.py:259 | `unexpected gh identity; no credential changes attempted` | `unexpected_identity` |
| writer_github.py:261 | `Project owner mismatch` | `project_identity_changed` |
| writer_github.py:262 | `Project identity mismatch` | `project_identity_changed` |
| writer_github.py:265 | `target identity/head/state mismatch` | `target_state_changed` |
| writer_github.py:267 | `unsupported Project field definition` | `unsupported_field_definition` |
| writer_github.py:277 | `Project or target state changed` | `project_or_target_changed` |
| writer_github.py:279 | `Project/target changed during pagination` | `pagination_metadata_changed` |
| writer_github.py:284 | `redacted Project content` | `unreadable_node` |
| writer_github.py:289 | `duplicate item/content identity` | `duplicate_identity` |
| writer_github.py:293 | `pagination cursor repeated` | `pagination_cursor_repeated` |
| writer_github.py:294 | `inconsistent item count` | `pagination_count_inconsistent` |
| writer_github.py:296 | `incomplete Project item read` | `pagination_incomplete` |
| writer_github.py:298 | `membership count changed during pagination` | `pagination_count_changed` |
| writer_github.py:306 | `Project page budget exhausted` | `page_budget_exhausted` |
| writer_github.py:309 | `transport disabled or operation already attempted` | `mutation_not_armed` |
| writer_github.py:310 | `mutation scope mismatch` | `mutation_scope_mismatch` |
| writer_github.py:312 | `complete preflight read required` | `preflight_required` |
| writer_github.py:318 | `mutation response uncertain` | `mutation_outcome_uncertain` |
| writer_github.py:320 | `mutation acknowledgment mismatch` | `mutation_acknowledgment_mismatch` |
| writer_github.py:323 | `add outcome uncertain; use read-only recovery, never resend` | `mutation_outcome_uncertain` |
