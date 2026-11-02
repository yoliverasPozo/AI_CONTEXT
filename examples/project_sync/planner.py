"""Pure, conservative reconciliation proposals from a complete snapshot."""
import copy
import re


class PlanError(ValueError):
    """Input or observation is insufficient for a safe complete proposal."""


REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
NAME = re.compile(r"[A-Za-z0-9_-]+\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
MARKER = re.compile(r"<!--\s*ai-context-next:\s*(work|codex|chatgpt|blocked)\s*-->", re.I)
LIMITS = {"max_calls": 100, "max_pages": 100, "page_size": 50,
          "rate_floor": 100, "max_handoff_bytes": 65536}


def require(condition, message):
    if not condition:
        raise PlanError(message)


def positive(value):
    return type(value) is int and value > 0


def validate_config(config):
    """Validate explicit scope; return a detached config with bounded defaults."""
    require(type(config) is dict, "configuration must be an object")
    result = copy.deepcopy(config)
    project = result.get("project", {})
    require(type(project) is dict and type(project.get("owner")) is str
            and NAME.fullmatch(project["owner"]), "invalid project owner")
    require(project.get("owner_type") in ("user", "organization")
            and positive(project.get("number")), "invalid project selection")
    repos = result.get("repositories")
    require(type(repos) is list and 0 < len(repos) <= 100, "explicit repository allowlist required")
    seen = set()
    for repo in repos:
        require(type(repo) is dict and type(repo.get("name")) is str
                and REPOSITORY.fullmatch(repo["name"]), "invalid repository allowlist entry")
        require(repo["name"].lower() not in seen, "duplicate allowlist repository")
        seen.add(repo["name"].lower())
        issues = repo.setdefault("issues", [])
        require(type(issues) is list and all(positive(n) for n in issues)
                and len(issues) == len(set(issues)) and len(issues) <= 1000,
                "invalid issue allowlist")
        paths = repo.setdefault("handoffs", {})
        require(type(paths) is dict and len(paths) <= 1000, "invalid handoff allowlist")
        for number, path in paths.items():
            require(type(number) is str and number.isascii() and number.isdigit()
                    and int(number) > 0 and str(int(number)) == number,
                    "invalid handoff PR number")
            require(type(path) is str and path.startswith("docs/sessions/")
                    and path.endswith(".md") and "\\" not in path
                    and all(p not in ("", ".", "..") for p in path.split("/"))
                    and not any(ord(c) < 32 for c in path), "invalid handoff path")
    require(result.get("actor_field") == "Next actor",
            "prototype actor field must be exactly Next actor; other fields are never projected")
    roles = result.get("roles")
    require(type(roles) is dict and roles and set(roles) <= {"work", "codex", "chatgpt"},
            "explicit role mappings required")
    for role in roles.values():
        require(type(role) is dict and all(type(role.get(k)) is str and role[k].strip()
                for k in ("owner", "value")), "invalid role mapping")
    limits = result.setdefault("limits", {})
    require(type(limits) is dict and set(limits) <= set(LIMITS), "invalid limits")
    for name, default in LIMITS.items():
        value = limits.setdefault(name, default)
        require(positive(value), "limits must be positive integers")
    require(limits["page_size"] <= 100 and limits["max_calls"] <= 500
            and limits["max_pages"] <= 1000 and limits["max_handoff_bytes"] <= 262144,
            "limits exceed prototype bounds")
    return result


def identity(content):
    require(type(content) is dict, "missing project content; identity cannot be established")
    require(type(content.get("id")) is str and content["id"], "missing content identity")
    require(content.get("kind") in ("PullRequest", "Issue", "DraftIssue"), "unknown content type")
    if content["kind"] != "DraftIssue":
        require(type(content.get("repository")) is str
                and REPOSITORY.fullmatch(content["repository"])
                and positive(content.get("number")), "invalid repository content identity")
    return content["id"]


def coordination_section(text):
    """Select one real heading outside Markdown fences, not a quoted example."""
    sections, current, fenced_section, fence = [], None, False, None
    for line in text.splitlines():
        if fence is not None:
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{" + str(fence[1]) + r",}\s*", line):
                fence = None
            continue
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if opening:
            fence = (opening[1][0], len(opening[1]))
            if current is not None:
                fenced_section = True
            continue
        if re.fullmatch(r"## Coordination\s*", line):
            if current is not None:
                sections.append((current, fenced_section))
            current, fenced_section = [], False
        elif re.match(r"^## ", line):
            if current is not None:
                sections.append((current, fenced_section))
            current, fenced_section = None, False
        elif current is not None:
            current.append(line)
    if current is not None:
        sections.append((current, fenced_section))
    require(len(sections) == 1, "missing or ambiguous unfenced Coordination section")
    require(not sections[0][1], "fenced coordination metadata unsupported")
    return sections[0][0]


def ready_handoff(config, candidate, records):
    """Admit only a literal, configured, exact-head transfer; never execute text."""
    markers = MARKER.findall(candidate.get("body", ""))
    marker_starts = re.findall(r"<!--\s*ai-context-next\s*:", candidate.get("body", ""), re.I)
    require(len(markers) == len(marker_starts) == 1 and markers[0].lower() in config["roles"],
            "missing or conflicting routing marker")
    role = markers[0].lower()
    labels = candidate.get("labels")
    require(type(labels) is list and all(type(x) is str for x in labels), "invalid labels")
    managed = [label for label in labels if label.startswith("ai-next:")]
    require(managed == ["ai-next:" + role], "label and marker conflict")
    matches = [record for record in records if record.get("repository") == candidate["repository"]
               and record.get("number") == candidate["number"]]
    require(len(matches) == 1, "handoff verification unavailable or ambiguous")
    record = matches[0]
    repo = next(r for r in config["repositories"] if r["name"] == candidate["repository"])
    require(repo["handoffs"].get(str(candidate["number"])) == record.get("path"),
            "handoff path is not explicitly configured")
    head = candidate.get("head_sha")
    require(type(head) is str and SHA.fullmatch(head) and record.get("head_sha") == head
            and record.get("observed_head_sha") == head, "stale or unknown head observation")
    require(type(record.get("blob_sha")) is str and SHA.fullmatch(record["blob_sha"]),
            "missing handoff blob revision")
    text = record.get("text")
    require(type(text) is str and len(text.encode("utf-8")) <= config["limits"]["max_handoff_bytes"],
            "handoff content unavailable or too large")
    # Deliberately narrow Markdown subset: one Coordination section; no YAML,
    # code fences, execution, fuzzy ownership matching or prose inference.
    metadata = {}
    for line in coordination_section(text):
        match = re.fullmatch(r"(Task ID|Status|Next owner|Repository): ([^\r\n]+)", line)
        if re.match(r"\s*(Task ID|Status|Next owner|Repository)\s*:", line, re.I):
            require(match is not None, "malformed coordination metadata")
        if match:
            require(match[1] not in metadata, "duplicate coordination metadata")
            metadata[match[1]] = match[2].strip()
    expected = config["roles"][role]
    require(metadata.get("Status") == "ready" and metadata.get("Next owner") == expected["owner"]
            and metadata.get("Repository") == candidate["repository"] and metadata.get("Task ID"),
            "journal owner, status or repository conflict")
    return {"role": role, "owner": expected["owner"], "value": expected["value"],
            "blob_sha": record["blob_sha"], "task_id": metadata["Task ID"]}


def plan(config, snapshot, cursor=None):
    """Return proposals only; no mutation, notification, persistence or network."""
    config = validate_config(config)
    require(type(snapshot) is dict and snapshot.get("schema_version") == 1
            and snapshot.get("complete") is True, "complete schema version 1 snapshot required")
    project = snapshot.get("project", {})
    require(type(project) is dict and all(project.get(k) == v for k, v in config["project"].items())
            and type(project.get("id")) is str and project["id"], "project identity mismatch")
    for key in ("pull_requests", "issues", "handoffs"):
        require(type(snapshot.get(key)) is list, "snapshot collection missing")
    require(all(type(r) is dict for r in snapshot["handoffs"]), "invalid handoff observation")
    require(type(project.get("items")) is list, "project items missing")
    repos = {r["name"]: r for r in config["repositories"]}
    existing, item_ids, logical = {}, set(), {}
    for item in project["items"]:
        require(type(item) is dict and type(item.get("id")) is str and item["id"]
                and type(item.get("archived")) is bool and type(item.get("fields")) is dict,
                "invalid project item")
        content_id = identity(item.get("content"))
        require(item["id"] not in item_ids and content_id not in existing,
                "duplicate project item or content identity")
        item_ids.add(item["id"]); existing[content_id] = item
        content = item["content"]
        if content["kind"] != "DraftIssue":
            key = (content["kind"], content["repository"], content["number"])
            require(key not in logical, "duplicate logical content identity")
            logical[key] = content_id
    candidates, candidate_logical = {}, {}
    for content in snapshot["pull_requests"] + snapshot["issues"]:
        content_id = identity(content)
        require(content["kind"] != "DraftIssue", "draft candidate unsupported")
        key = (content["kind"], content["repository"], content["number"])
        require(content_id not in candidates and key not in candidate_logical,
                "duplicate candidate identity")
        require(key not in logical or logical[key] == content_id, "content identity changed")
        if content_id in existing:
            previous = existing[content_id]["content"]
            require((previous["kind"], previous["repository"], previous["number"]) == key,
                    "content identity conflict")
        require(content.get("state") in ("OPEN", "CLOSED", "MERGED"), "unknown content state")
        if content["kind"] == "PullRequest":
            require(type(content.get("merged")) is bool and type(content.get("body")) is str,
                    "invalid PR lifecycle or description")
        candidates[content_id] = content; candidate_logical[key] = content_id
    for content_id, item in existing.items():
        content = item["content"]
        require(not (content["kind"] == "PullRequest" and content["repository"] in repos)
                or content_id in candidates, "tracked PR lifecycle was not refreshed")
    cursor = cursor if cursor is not None else {"schema_version": 1, "observed_keys": []}
    require(type(cursor) is dict and cursor.get("schema_version") == 1
            and type(cursor.get("observed_keys")) is list
            and len(cursor["observed_keys"]) <= 100000, "invalid notification cursor")
    seen_keys = set()
    for key in cursor["observed_keys"]:
        require(type(key) is list and len(key) == 5 and type(key[0]) is str
                and positive(key[1]) and all(type(v) is str for v in key[2:]), "invalid notification key")
        seen_keys.add(tuple(key))
    result = {"schema_version": 1, "mode": "plan-only", "project_id": project["id"],
              "additions": [], "field_proposals": [], "terminal_suggestions": [],
              "notification_proposals": [], "diagnostics": []}
    proposed_keys = set(seen_keys)
    for content_id, content in sorted(candidates.items()):
        repo = repos.get(content["repository"])
        if not repo or (content["kind"] == "Issue" and content["number"] not in repo["issues"]):
            continue
        item = existing.get(content_id)
        terminal = content["state"] != "OPEN" or content.get("merged", False)
        if terminal:
            if item:
                result["terminal_suggestions"].append({"item_id": item["id"],
                    "content_id": content_id, "lifecycle": "merged" if content.get("merged") else "closed",
                    "preserved_fields": copy.deepcopy(item["fields"]), "status_write": False})
            continue
        if not item:
            result["additions"].append({"content_id": content_id, "repository": content["repository"],
                                       "number": content["number"], "kind": content["kind"]})
        if content["kind"] != "PullRequest" or (item and item["archived"]):
            continue
        try:
            verified = ready_handoff(config, content, snapshot["handoffs"])
        except PlanError as error:
            result["diagnostics"].append({"content_id": content_id, "handoff_state": "unknown-or-conflict",
                                          "reason": str(error)})
            continue
        if item and item["fields"].get(config["actor_field"]) in (None, ""):
            result["field_proposals"].append({"item_id": item["id"], "field": config["actor_field"],
                "before": item["fields"].get(config["actor_field"]), "after": verified["value"],
                "head_sha": content["head_sha"], "handoff_blob_sha": verified["blob_sha"]})
        key = (content["repository"], content["number"], content["head_sha"],
               verified["owner"], verified["blob_sha"])
        if key not in seen_keys:
            result["notification_proposals"].append({"key": list(key), "task_id": verified["task_id"],
                "delivery": "not-sent", "acknowledgment": "not-inferred"})
            proposed_keys.add(key)
    result["proposed_cursor"] = {"schema_version": 1,
        "observed_keys": [list(key) for key in sorted(proposed_keys)]}
    return result
