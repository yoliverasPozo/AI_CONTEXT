"""Guarded one-item addition policy. Rollback/recovery never perform mutations."""
import copy
import re
import time

from .writer_journal import canonical, sha


class WriterError(ValueError):
    """Expected scope/state or explicit operation permission was not established."""


def require(condition, message):
    if not condition:
        raise WriterError(message)


def identifier(value):
    return type(value) is str and 0 < len(value) <= 256 and not any(c.isspace() or ord(c) < 32 for c in value)


def normalize(source):
    """Reject incomplete/duplicate data; canonicalize unordered field/item sets."""
    require(type(source) is dict and set(source) == {"complete", "project", "items", "target"}
            and source["complete"] is True, "complete writer snapshot required")
    result = copy.deepcopy(source)
    project, target, items = result["project"], result["target"], result["items"]
    require(type(project) is dict and set(project) == {"id", "owner", "owner_type", "number", "public", "closed", "fields"},
            "invalid Project selection")
    require(identifier(project["id"]) and identifier(project["owner"]) and project["owner_type"] in ("user", "organization")
            and type(project["number"]) is int and project["number"] > 0
            and type(project["public"]) is bool and project["closed"] is False, "invalid or closed Project")
    require(type(target) is dict and set(target) == {"id", "repository", "number", "head_sha", "state"},
            "invalid single PR target")
    require(identifier(target["id"]) and type(target["repository"]) is str
            and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", target["repository"])
            and target["repository"].split("/")[0] == project["owner"]
            and type(target["number"]) is int and target["number"] > 0
            and type(target["head_sha"]) is str and re.fullmatch(r"[0-9a-f]{40}", target["head_sha"])
            and target["state"] == "OPEN", "PR target must be same-owner, open and exact-head")
    require(type(project["fields"]) is list and len(project["fields"]) <= 100, "invalid field definitions")
    definitions = project["fields"]
    require(all(type(f) is dict and identifier(f.get("id")) and type(f.get("name")) is str
                and type(f.get("dataType")) is str for f in definitions), "invalid field identity")
    field_ids = {f["id"] for f in definitions}
    require(len(field_ids) == len(definitions), "duplicate field definition")
    project["fields"] = sorted(definitions, key=lambda f: f["id"])
    require(type(items) is list and len(items) <= 10000, "item bound exceeded")
    item_ids, content_ids = set(), set()
    for item in items:
        require(type(item) is dict and set(item) == {"id", "content_id", "kind", "archived", "values"}
                and identifier(item["id"]) and identifier(item["content_id"])
                and item["kind"] in ("PullRequest", "Issue", "DraftIssue") and type(item["archived"]) is bool,
                "invalid or redacted Project item")
        require(item["id"] not in item_ids and item["content_id"] not in content_ids, "duplicate item/content identity")
        item_ids.add(item["id"]); content_ids.add(item["content_id"])
        require(type(item["values"]) is list and len(item["values"]) <= 100, "invalid item fields")
        seen = set()
        for value in item["values"]:
            require(type(value) is dict and set(value) == {"field_id", "kind", "value"}
                    and value["field_id"] in field_ids and value["field_id"] not in seen
                    and value["kind"] in ("Text", "SingleSelect", "Number", "Date", "Iteration", "MultiSelect",
                        "Repository", "Label", "User", "Milestone", "Reviewer", "PullRequest"),
                    "unsupported or duplicate populated field")
            seen.add(value["field_id"])
        item["values"] = sorted(item["values"], key=lambda v: v["field_id"])
    result["items"] = sorted(items, key=lambda item: item["id"])
    try:
        require(len(canonical(result)) <= 8 * 1024 * 1024, "snapshot exceeds receipt bound")
    except (TypeError, ValueError):
        raise WriterError("non-JSON or non-finite field value") from None
    return result


def prepare(source, operation_id, now, expires_at):
    require(type(operation_id) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", operation_id), "invalid operation ID")
    require(type(now) is int and type(expires_at) is int and now < expires_at <= now+3600,
            "proposal must expire within one hour")
    body = {"schema_version": 1, "operation_id": operation_id, "created_at": now,
            "expires_at": expires_at, "before": normalize(source)}
    return dict(body, sha256=sha(body))


def check_proposal(proposal):
    require(type(proposal) is dict and set(proposal) == {"schema_version", "operation_id", "created_at", "expires_at", "before", "sha256"},
            "invalid proposal schema")
    require(proposal["schema_version"] == 1 and type(proposal["schema_version"]) is int, "unsupported proposal version")
    expected = prepare(proposal["before"], proposal["operation_id"], proposal["created_at"], proposal["expires_at"])
    require(proposal == expected, "proposal digest or canonical state mismatch")
    return proposal["before"]


def validate_approval(proposal, approval, now, enabled=False, execute=False):
    require(enabled is True and execute is True, "writer disabled; explicit enablement and execution are required")
    before = check_proposal(proposal)
    require(type(approval) is dict and set(approval) == {"action", "operation_id", "proposal_sha256", "project_id", "content_id", "expires_at"},
            "exact owner approval record required")
    require(approval["action"] == "add_one" and approval["operation_id"] == proposal["operation_id"]
            and approval["proposal_sha256"] == proposal["sha256"]
            and approval["project_id"] == before["project"]["id"] and approval["content_id"] == before["target"]["id"],
            "approval does not match this single operation")
    require(type(now) is int and type(approval["expires_at"]) is int
            and proposal["created_at"] <= now < approval["expires_at"] <= proposal["expires_at"], "approval expired or not current")
    return before


def matching_target(source):
    return [item for item in source["items"] if item["content_id"] == source["target"]["id"]]


def addition_check(before, current):
    """Return target iff only it differs; never normalize away original state."""
    require(before["project"] == current["project"] and before["target"] == current["target"], "Project or target state changed")
    target = matching_target(current)
    existing = matching_target(before)
    if existing:
        require(before == current, "existing item or Project changed")
        return target
    old = {i["id"]: i for i in before["items"]}
    new = {i["id"]: i for i in current["items"]}
    require(all(new.get(key) == value for key, value in old.items()), "original item/field state changed")
    extra = [value for key, value in new.items() if key not in old]
    require(extra == target, "unrelated Project membership changed")
    return target


def apply(proposal, backend, journal, *, enabled=False, execute=False, approval=None, now=None, clock=None):
    before = validate_approval(proposal, approval, now, enabled, execute)
    with journal.lock():
        events = journal.events()
        require(events[0]["data"]["proposal"] == proposal, "journal belongs to another proposal")
        kinds = [event["kind"] for event in events]
        if "complete" in kinds or "no_op" in kinds:
            return copy.deepcopy(next(e["data"]["result"] for e in reversed(events) if e["kind"] in ("complete", "no_op")))
        if "intent" in kinds:
            return {"status": "recovery_required", "mutation_retried": False}
        current = normalize(backend.read())
        found = addition_check(before, current)
        if found:
            result = {"status": "already_present", "item_id": found[0]["id"], "ownership": "not_owned"}
            journal.append("no_op", {"before": current, "result": result})
            return result
        require(before == current, "expected state changed")
        validate_approval(proposal, approval, int((clock or time.time)()), enabled, execute)
        journal.append("intent", {"proposal_sha256": proposal["sha256"]})
        # Journal fsync can itself consume the remaining approval window.
        # Expiration here leaves a spent intent, never a retryable operation.
        validate_approval(proposal, approval, int((clock or time.time)()), enabled, execute)
        try:
            item_id = backend.add(before["project"]["id"], before["target"]["id"], proposal["operation_id"])
            require(identifier(item_id), "invalid mutation response identity")
        except Exception:
            result = {"status": "uncertain", "ownership": "unknown", "mutation_retried": False}
            journal.append("uncertain", {"result": result})
            return result
        journal.append("acknowledged", {"item_id": item_id, "ownership": "not_proven"})
        try:
            after = normalize(backend.read())
            target = addition_check(before, after)
            require(len(target) == 1 and target[0]["id"] == item_id and not target[0]["archived"], "add readback identity mismatch")
        except Exception:
            result = {"status": "needs_review", "item_id": item_id, "ownership": "not_proven", "mutation_retried": False}
            journal.append("needs_review", {"result": result})
            return result
        result = {"status": "verified_present", "item_id": item_id, "ownership": "not_proven"}
        journal.append("complete", {"after": after, "result": result, "ownership": "not_proven"})
        return result


def recover(journal, backend):
    with journal.lock():
        return _recover_locked(journal, backend)


def _recover_locked(journal, backend):
    events = journal.events()
    proposal = events[0]["data"]["proposal"]
    before = check_proposal(proposal)
    current = normalize(backend.read())
    found = addition_check(before, current)
    kinds = [e["kind"] for e in events]
    require("intent" in kinds, "no mutation intent to reconcile")
    acknowledged = [e["data"]["item_id"] for e in events if e["kind"] == "acknowledged"]
    if found and acknowledged:
        require(found[0]["id"] == acknowledged[-1], "recovery response identity conflict")
    result = {"status": "present_after_uncertain" if found else "absent_after_uncertain",
            "ownership": "unknown", "item_id": found[0]["id"] if found else None,
            "mutation_retried": False, "late_commit_excluded": False}
    journal.append("reconciled", {"observed": current, "result": result})
    return result


def rollback_proposal(journal, source):
    events = journal.events()
    completed = [e for e in events if e["kind"] == "complete"]
    require(len(completed) == 1, "only a complete add receipt permits rollback assessment")
    before = check_proposal(events[0]["data"]["proposal"])
    require(not matching_target(before), "preexisting items cannot be rollback candidates")
    current = normalize(source)
    require(current == completed[0]["data"]["after"], "rollback state changed; preserve human work")
    target = matching_target(current)
    require(len(target) == 1 and not target[0]["archived"] and target[0]["id"] == completed[0]["data"]["result"]["item_id"],
            "rollback item identity changed")
    return {"action": "manual_removal_review", "project_id": before["project"]["id"],
            "content_id": before["target"]["id"], "item_id": target[0]["id"],
            "executable": False, "ownership_proven": False, "separate_authorization_required": True}
