"""Bounded GitHub GraphQL reads through an existing gh login; no mutations."""
import json
import subprocess

from .planner import PlanError, SHA, identity, positive, require, validate_config


PAGE = "totalCount pageInfo { hasNextPage endCursor }"
IDENTITY = """__typename ... on PullRequest { id number repository { nameWithOwner } }
... on Issue { id number repository { nameWithOwner } } ... on DraftIssue { id }"""
PR = """__typename id number repository { nameWithOwner } state merged headRefOid body
labels(first: 100) { nodes { name } totalCount pageInfo { hasNextPage endCursor } }"""
FIELD = "field { ... on ProjectV2FieldCommon { id name } }"
VALUES = """__typename
... on ProjectV2ItemFieldSingleSelectValue { name FIELD }
... on ProjectV2ItemFieldTextValue { text FIELD }
... on ProjectV2ItemFieldNumberValue { number FIELD }
... on ProjectV2ItemFieldDateValue { date FIELD }
... on ProjectV2ItemFieldIterationValue { title FIELD }""".replace("FIELD", FIELD)
RATE = "rateLimit { remaining cost }"


def gh_transport(document, variables, *, timeout=45):
    completed = subprocess.run(["gh", "api", "graphql", "--hostname", "github.com", "--input", "-"],
        input=json.dumps({"query": document, "variables": variables}), capture_output=True,
        text=True, encoding="utf-8", timeout=timeout, check=True)
    require(len(completed.stdout.encode("utf-8")) <= 16 * 1024 * 1024,
            "GraphQL response exceeds 16 MiB limit")
    return json.loads(completed.stdout)


class GhClient:
    """Read budget/rate guard shared by all requests in a collection."""
    def __init__(self, limits, transport=None):
        self.limits = limits
        self.transport = transport or gh_transport
        self.calls = 0
        self.remaining = None

    def query(self, document, variables):
        require(document.lstrip().startswith("query ") and "mutation" not in document,
                "only read queries are supported")
        require(self.calls < self.limits["max_calls"], "GraphQL call budget exhausted")
        self.calls += 1
        try:
            response = self.transport(document, variables)
        except subprocess.CalledProcessError as error:
            detail = (error.stderr or "") + (error.stdout or "")
            if "read:project" in detail or "project scope" in detail.lower():
                raise PlanError("existing gh login lacks read:project access; no scopes were changed") from None
            raise PlanError("GitHub read failed; check existing login and repository/project access") from None
        except (OSError, subprocess.TimeoutExpired, ValueError):
            raise PlanError("GitHub read unavailable, timed out or returned invalid JSON") from None
        require(type(response) is dict and not response.get("errors"),
                "GraphQL returned errors; no partial plan produced")
        data = response.get("data")
        require(type(data) is dict, "GraphQL data missing")
        rate = data.get("rateLimit")
        require(type(rate) is dict and type(rate.get("remaining")) is int
                and type(rate.get("cost")) is int and rate["cost"] >= 0,
                "GraphQL rate-limit evidence missing")
        self.remaining = rate["remaining"]
        require(self.remaining >= self.limits["rate_floor"], "GraphQL rate floor reached; collection stopped")
        return data


def connection_page(connection):
    require(type(connection) is dict and type(connection.get("nodes")) is list
            and type(connection.get("totalCount")) is int and connection["totalCount"] >= 0,
            "missing or malformed collection page")
    page = connection.get("pageInfo")
    require(type(page) is dict and type(page.get("hasNextPage")) is bool,
            "pagination evidence missing")
    require(not page["hasNextPage"] or (type(page.get("endCursor")) is str and page["endCursor"]),
            "next-page cursor missing")
    require(all(type(node) is dict for node in connection["nodes"]), "collection contains unreadable node")
    return connection["nodes"], connection["totalCount"], page


def whole_connection(connection):
    nodes, total, page = connection_page(connection)
    require(not page["hasNextPage"] and total == len(nodes),
            "nested collection truncated; no partial plan produced")
    return nodes


def pages(client, config, document, variables, extract):
    cursor, cursors, nodes, total, identities = None, set(), [], None, set()
    for _ in range(config["limits"]["max_pages"]):
        data = client.query(document, dict(variables, cursor=cursor, size=config["limits"]["page_size"]))
        try:
            connection = extract(data)
        except (KeyError, TypeError):
            raise PlanError("collection unavailable; check scope and access") from None
        batch, count, page = connection_page(connection)
        require(total is None or total == count, "collection count changed during pagination")
        total = count
        for node in batch:
            node_id = node.get("id")
            require(type(node_id) is str and node_id and node_id not in identities,
                    "missing or duplicate paginated node identity")
            identities.add(node_id)
        nodes.extend(batch)
        require(len(nodes) <= total, "collection count is inconsistent")
        if not page["hasNextPage"]:
            require(len(nodes) == total, "collection ended before all records were read")
            return nodes
        cursor = page["endCursor"]
        require(cursor not in cursors, "pagination cursor repeated")
        cursors.add(cursor)
    raise PlanError("collection page budget exhausted")


def normalize_identity(node):
    require(type(node) is dict, "unreadable project content")
    value = {"id": node.get("id"), "kind": node.get("__typename")}
    if value["kind"] != "DraftIssue":
        repository = node.get("repository")
        require(type(repository) is dict, "repository identity unavailable")
        value.update(repository=repository.get("nameWithOwner"), number=node.get("number"))
    identity(value)
    return value


def normalize_pr(node):
    value = normalize_identity(node)
    require(value["kind"] == "PullRequest" and type(node.get("body")) is str
            and type(node.get("merged")) is bool and node.get("state") in ("OPEN", "CLOSED", "MERGED")
            and type(node.get("headRefOid")) is str and SHA.fullmatch(node["headRefOid"]),
            "PR observation incomplete")
    labels = whole_connection(node.get("labels"))
    require(all(type(label.get("name")) is str for label in labels), "label names unavailable")
    value.update(state=node["state"], merged=node["merged"], head_sha=node["headRefOid"],
                 body=node["body"], labels=[label["name"] for label in labels])
    return value


def collect(config, client):
    """Collect one bounded observation, including tracked terminal/archived PRs."""
    config = validate_config(config)
    project = config["project"]
    project_id = None
    field_definitions = None
    project_document = """query ProjectItems($owner: String!, $number: Int!, $cursor: String, $size: Int!) {
      owner: OWNER(login: $owner) { projectV2(number: $number) { id
        fields(first: 100) { nodes { ... on ProjectV2FieldCommon { id name dataType } } PAGE }
        items(first: $size, after: $cursor, archivedStates: [ARCHIVED, NOT_ARCHIVED]) {
          nodes { id isArchived content { IDENTITY } fieldValues(first: 100) { nodes { VALUES } PAGE } } PAGE
        }
      } } RATE
    }""".replace("OWNER", project["owner_type"]).replace("IDENTITY", IDENTITY).replace("VALUES", VALUES)
    project_document = project_document.replace("PAGE", PAGE).replace("RATE", RATE)

    def project_connection(data):
        nonlocal project_id, field_definitions
        observed = data["owner"]["projectV2"]
        require(type(observed) is dict and type(observed.get("id")) is str,
                "project unavailable; check existing access")
        require(project_id is None or project_id == observed["id"], "project changed during pagination")
        project_id = observed["id"]
        fields = whole_connection(observed.get("fields"))
        require(field_definitions is None or field_definitions == fields,
                "project fields changed during pagination")
        field_definitions = fields
        return observed["items"]

    raw_items = pages(client, config, project_document,
                      {"owner": project["owner"], "number": project["number"]}, project_connection)
    actor_fields = [f for f in field_definitions if f.get("name") == config["actor_field"]]
    require(len(actor_fields) == 1 and actor_fields[0].get("dataType") in ("SINGLE_SELECT", "TEXT"),
            "actor field missing, ambiguous or unsupported")
    items = []
    for node in raw_items:
        require(type(node.get("isArchived")) is bool, "archive evidence missing")
        fields = {}
        for value in whole_connection(node.get("fieldValues")):
            definition = value.get("field")
            if definition is None:
                require(type(value.get("__typename")) is str and value["__typename"] not in (
                    "ProjectV2ItemFieldSingleSelectValue", "ProjectV2ItemFieldTextValue",
                    "ProjectV2ItemFieldNumberValue", "ProjectV2ItemFieldDateValue",
                    "ProjectV2ItemFieldIterationValue"), "project field identity unavailable")
                # Unhandled field types are never written; the selected actor
                # field's supported type was independently checked above.
                continue
            require(type(definition) is dict and type(definition.get("name")) is str,
                    "project field identity unavailable")
            name = definition["name"]
            require(name not in fields, "duplicate project field value")
            keys = [key for key in ("name", "text", "number", "date", "title") if key in value]
            require(len(keys) == 1, "project field value unavailable")
            fields[name] = value[keys[0]]
        items.append({"id": node["id"], "archived": node["isArchived"],
                      "content": normalize_identity(node.get("content")), "fields": fields})
    repo_document = """query OpenPRs($owner: String!, $repo: String!, $cursor: String, $size: Int!) {
      repository(owner: $owner, name: $repo) { pullRequests(first: $size, after: $cursor, states: OPEN) {
        nodes { PR } PAGE
      } } RATE
    }""".replace("PR }", PR + " }").replace("PAGE", PAGE).replace("RATE", RATE)
    node_document = "query TrackedPR($id: ID!) { node(id: $id) { ... on PullRequest { PR } } RATE }"
    node_document = node_document.replace("PR }", PR + " }").replace("RATE", RATE)
    issue_document = """query RelevantIssue($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) { issue(number: $number) {
        __typename id number state repository { nameWithOwner }
      } } RATE
    }""".replace("RATE", RATE)
    prs, issues = {}, []
    for repo in config["repositories"]:
        owner, name = repo["name"].split("/")
        variables = {"owner": owner, "repo": name}
        raw_prs = pages(client, config, repo_document, variables,
                        lambda data: data["repository"]["pullRequests"])
        for node in raw_prs:
            value = normalize_pr(node)
            require(value["repository"] == repo["name"] and value["state"] == "OPEN"
                    and value["id"] not in prs, "unexpected open PR identity or state")
            prs[value["id"]] = value
        for item in items:
            content = item["content"]
            if content["kind"] == "PullRequest" and content["repository"] == repo["name"] and content["id"] not in prs:
                value = normalize_pr(client.query(node_document, {"id": content["id"]}).get("node"))
                require(all(value[k] == content[k] for k in ("id", "repository", "number")),
                        "tracked PR identity changed")
                prs[value["id"]] = value
        for number in repo["issues"]:
            data = client.query(issue_document, dict(variables, number=number))
            try:
                node = data["repository"]["issue"]
            except (KeyError, TypeError):
                raise PlanError("configured issue unavailable") from None
            value = normalize_identity(node)
            require(value["kind"] == "Issue" and value["repository"] == repo["name"]
                    and value["number"] == number and node.get("state") in ("OPEN", "CLOSED"),
                    "configured issue identity or lifecycle unavailable")
            value["state"] = node["state"]
            issues.append(value)
    handoffs = []
    blob_document = """query HandoffBlob($owner: String!, $repo: String!, $expression: String!) {
      repository(owner: $owner, name: $repo) { object(expression: $expression) {
        __typename ... on Blob { oid text byteSize isTruncated isBinary }
      } } RATE
    }""".replace("RATE", RATE)
    for repo in config["repositories"]:
        owner, name = repo["name"].split("/")
        for value in list(prs.values()):
            path = repo["handoffs"].get(str(value["number"]))
            if value["repository"] != repo["name"] or value["state"] != "OPEN" or not path:
                continue
            data = client.query(blob_document, {"owner": owner, "repo": name,
                "expression": value["head_sha"] + ":" + path})
            try:
                blob = data["repository"]["object"]
            except (KeyError, TypeError):
                raise PlanError("handoff repository unavailable") from None
            # Missing journal is unknown, not a reason to suppress safe additions.
            if blob is None:
                continue
            require(type(blob) is dict and blob.get("__typename") == "Blob"
                    and blob.get("isTruncated") is False and blob.get("isBinary") is False
                    and type(blob.get("byteSize")) is int
                    and 0 <= blob["byteSize"] <= config["limits"]["max_handoff_bytes"]
                    and type(blob.get("text")) is str
                    and len(blob["text"].encode("utf-8")) == blob["byteSize"],
                    "handoff blob unreadable, truncated or exceeds limit")
            current = normalize_pr(client.query(node_document, {"id": value["id"]}).get("node"))
            require(all(current[k] == value[k] for k in ("id", "repository", "number")),
                    "handoff PR identity changed")
            handoffs.append({"repository": value["repository"], "number": value["number"], "path": path,
                "head_sha": value["head_sha"], "observed_head_sha": current["head_sha"],
                "blob_sha": blob.get("oid"), "text": blob["text"]})
            # Re-read state, marker and label as well as head. A same-head
            # description/label change must not keep an old admitted owner.
            prs[value["id"]] = current
    return {"schema_version": 1, "complete": True,
        "project": dict(project, id=project_id, items=items),
        "pull_requests": list(prs.values()), "issues": issues, "handoffs": handoffs,
        "read_stats": {"calls": client.calls, "remaining": client.remaining}}
