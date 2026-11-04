"""Fixed failure vocabulary and bounded evidence; never persist exception text."""
import re
import subprocess


# These are internal static validation messages, never echoed remote messages.
MESSAGES = {
    "Project or target state changed":"project_or_target_changed",
    "original item/field state changed":"original_item_changed",
    "unrelated Project membership changed":"unexpected_membership",
    "existing item or Project changed":"existing_item_changed",
    "target absent after acknowledgment":"target_absent",
    "target response item differs":"target_item_mismatch",
    "target archived after acknowledgment":"target_archived",
    "duplicate item/content identity":"duplicate_identity",
    "GraphQL call budget exhausted":"call_budget_exhausted",
    "GraphQL rate floor reached; collection stopped":"rate_floor_reached",
    "GraphQL rate-limit evidence missing":"rate_evidence_missing",
    "GraphQL returned errors; no partial plan produced":"graphql_error",
    "GraphQL data missing":"response_shape_invalid",
    "GitHub read failed; check existing login and repository/project access":"transport_error",
    "existing gh login lacks read:project access; no scopes were changed":"read_access_denied",
    "GitHub read unavailable, timed out or returned invalid JSON":"transport_or_json_error",
    "nested collection truncated; no partial plan produced":"nested_collection_incomplete",
    "missing or malformed collection page":"page_shape_invalid",
    "pagination evidence missing":"pagination_invalid",
    "next-page cursor missing":"pagination_invalid",
    "collection contains unreadable node":"unreadable_node",
    "Project/target changed during pagination":"pagination_metadata_changed",
    "membership count changed during pagination":"pagination_count_changed",
    "inconsistent item count":"pagination_count_inconsistent",
    "incomplete Project item read":"pagination_incomplete",
    "pagination cursor repeated":"pagination_cursor_repeated",
    "Project page budget exhausted":"page_budget_exhausted",
    "target identity/head/state mismatch":"target_state_changed",
    "Project identity mismatch":"project_identity_changed",
    "Project owner mismatch":"project_identity_changed",
    "redacted Project content":"unreadable_node",
    "redacted or malformed populated relation":"unreadable_field_relation",
    "unsupported or incomplete populated field":"unsupported_field_value",
    "unknown populated field value":"unsupported_field_value",
    "unsupported Project field definition":"unsupported_field_definition",
    "Project/PR unavailable":"project_or_pr_unavailable",
    "unexpected gh identity; no credential changes attempted":"unexpected_identity",
    "unreadable field value":"unreadable_field_value",
    "field identity unavailable":"field_identity_unavailable",
    "missing populated collection":"field_collection_incomplete",
    "unreadable field relation":"unreadable_field_relation",
    "duplicate field relation":"duplicate_field_relation",
    "repository relation unreadable":"unreadable_field_relation",
    "milestone relation unreadable":"unreadable_field_relation",
    "transport disabled or operation already attempted":"mutation_not_armed",
    "mutation scope mismatch":"mutation_scope_mismatch",
    "complete preflight read required":"preflight_required",
    "mutation response uncertain":"mutation_outcome_uncertain",
    "mutation acknowledgment mismatch":"mutation_acknowledgment_mismatch",
    "add outcome uncertain; use read-only recovery, never resend":"mutation_outcome_uncertain",
    "verification elapsed budget exhausted":"verification_time_exhausted",
    "verification call budget exhausted":"verification_call_budget_exhausted",
    "verification evidence persistence failed":"verification_receipt_failed",
    "invalid or redacted Project item":"invalid_item",
    "invalid item fields":"invalid_item_fields",
    "unsupported or duplicate populated field":"invalid_item_fields",
    "non-JSON or non-finite field value":"invalid_item_fields",
    "snapshot exceeds receipt bound":"snapshot_bound_exceeded",
    "item bound exceeded":"snapshot_bound_exceeded",
    "complete writer snapshot required":"snapshot_incomplete",
    "invalid Project selection":"snapshot_scope_invalid",
    "invalid or closed Project":"snapshot_scope_invalid",
    "invalid single PR target":"snapshot_target_invalid",
    "PR target must be same-owner, open and exact-head":"snapshot_target_invalid",
    "invalid field definitions":"field_definitions_invalid",
    "invalid field identity":"field_definitions_invalid",
    "duplicate field definition":"field_definitions_invalid",
    "GraphQL response exceeds 16 MiB limit":"response_bound_exceeded",
    "only read queries are supported":"query_scope_invalid",
}
for _message in ("invalid writer config", "enabled must be an explicit boolean", "invalid Project scope",
                 "this pilot writer supports user-owned Projects only", "invalid target scope", "invalid read limits",
                 "unsafe read limit", "invalid verification limits", "unsafe verification limit",
                 "stabilization requires rate floor at least 200"):
    MESSAGES[_message] = "invalid_configuration"
CODES = frozenset(MESSAGES.values()) | {"transport_timeout", "transport_error", "unexpected_error"}


def error_code(error):
    """Only compare exact static arguments; no str/repr/traceback serialization."""
    if isinstance(error, (subprocess.TimeoutExpired, TimeoutError)):
        return "transport_timeout"
    if isinstance(error, (OSError, subprocess.CalledProcessError)):
        return "transport_error"
    # Unknown runtime exceptions cannot become retryable through message text.
    from .writer import WriterError
    from .planner import PlanError
    if not isinstance(error, (WriterError, PlanError)):
        return "unexpected_error"
    args = error.args
    if len(args) == 1 and type(args[0]) is str:
        return MESSAGES.get(args[0], "unexpected_error")
    return "unexpected_error"


def safe_evidence(value):
    """Whitelist schema, fixed enums, finite counters and SHA256s from a backend."""
    if type(value) is not dict:
        return {}
    out = {}
    counters = ("started_at_unix", "finished_at_unix", "max_calls", "max_pages", "page_size", "rate_floor",
                "read_calls_before", "read_calls_after", "points_before", "points_after")
    for key in counters:
        if type(value.get(key)) is int and 0 <= value[key] <= 10**12:
            out[key] = value[key]
    if type(value.get("failure_code")) is str and value["failure_code"] in CODES:
        out["failure_code"] = value["failure_code"]
    pages = value.get("pages")
    if type(pages) is list:
        out["pages"] = []
        for page in pages[:100]:
            if type(page) is not dict:
                continue
            entry = {}
            for key in ("call_index", "node_count", "total_count", "cost", "remaining"):
                if type(page.get(key)) is int and 0 <= page[key] <= 10**12:
                    entry[key] = page[key]
            if type(page.get("has_next_page")) is bool:
                entry["has_next_page"] = page["has_next_page"]
            for key in ("items_sha256", "fields_sha256", "target_sha256"):
                if type(page.get(key)) is str and re.fullmatch(r"[0-9a-f]{64}", page[key]):
                    entry[key] = page[key]
            out["pages"].append(entry)
    return out


def diagnostic(error, phase, backend):
    code = error_code(error)
    evidence = {}
    try:
        evidence = safe_evidence(getattr(backend, "read_evidence", None))
    except Exception:
        pass  # Diagnostics must not replace the original fail-closed outcome.
    if phase == "readback" and "failure_code" in evidence:
        code = evidence["failure_code"]
    return {"code":code, "phase":phase, "read_evidence":evidence}


def verification_summary(backend):
    try:
        value = getattr(backend, "verification_summary", None)
    except Exception:
        return {}
    if type(value) is not dict:
        return {}
    return {key:value[key] for key in ("max_attempts","max_seconds","max_calls","attempts","elapsed_milliseconds","read_calls")
            if type(value.get(key)) is int and 0<=value[key]<=10**12}
