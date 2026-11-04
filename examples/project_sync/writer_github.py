"""Bounded complete-state reader and one fixed, separately armed add transport."""
import copy
import re
import time

from .collector import GhClient, gh_transport, connection_page, whole_connection
from .writer import require, normalize, normalize_items, identifier, WriterError
from .writer_diagnostics import error_code, safe_evidence
from .writer_journal import sha

PAGE = "totalCount pageInfo { hasNextPage endCursor }"
FIELD = "field { ... on ProjectV2FieldCommon { id } }"
DEFINITIONS = """__typename
... on ProjectV2Field { id name dataType }
... on ProjectV2SingleSelectField { id name dataType options { id name description color } }
... on ProjectV2IterationField { id name dataType configuration {
 duration startDay iterations { id title startDate duration }
 completedIterations { id title startDate duration } } }"""
VALUES = """__typename
... on ProjectV2ItemFieldTextValue { FIELD text }
... on ProjectV2ItemFieldSingleSelectValue { FIELD optionId name }
... on ProjectV2ItemFieldNumberValue { FIELD number }
... on ProjectV2ItemFieldDateValue { FIELD date }
... on ProjectV2ItemFieldIterationValue { FIELD iterationId title startDate duration }
... on ProjectV2ItemFieldRepositoryValue { FIELD repository { id nameWithOwner } }
... on ProjectV2ItemFieldMilestoneValue { FIELD milestone { id title state dueOn } }
... on ProjectV2ItemFieldLabelValue { FIELD labels(first:100) { PAGE nodes { id name color description } } }
... on ProjectV2ItemFieldUserValue { FIELD users(first:100) { PAGE nodes { id login } } }
... on ProjectV2ItemFieldPullRequestValue { FIELD pullRequests(first:100) { PAGE nodes { id } } }
... on ProjectV2ItemFieldReviewerValue { FIELD reviewers(first:100) { PAGE nodes {
 __typename ... on User { id login } ... on Team { id slug } ... on Mannequin { id login } } } }
""".replace("FIELD", FIELD).replace("PAGE", PAGE)
# An unrecognized populated value (including new GitHub field types) is fatal.
# Do not filter it out: doing so would invent preservation evidence.
READ = """query WriterState($project:ID!, $target:ID!, $cursor:String, $size:Int!) {
viewer { login }
project: node(id:$project) { ... on ProjectV2 {
 id number public closed owner { __typename ... on User { login } ... on Organization { login } }
 fields(first:100) { PAGE nodes { DEFINITIONS } }
 items(first:$size, after:$cursor, archivedStates:[ARCHIVED, NOT_ARCHIVED]) { PAGE nodes {
 id isArchived content { __typename ... on PullRequest { id } ... on Issue { id } ... on DraftIssue { id } }
 fieldValues(first:100) { PAGE nodes { VALUES } } } }
} }
target: node(id:$target) { __typename ... on PullRequest {
 id number state headRefOid repository { nameWithOwner } } }
rateLimit { remaining cost }
}""".replace("DEFINITIONS", DEFINITIONS).replace("VALUES", VALUES).replace("PAGE", PAGE)

ADD_ONE = """mutation AddOne($project:ID!, $content:ID!, $operation:String!) {
addProjectV2ItemById(input:{projectId:$project, contentId:$content, clientMutationId:$operation}) {
 item { id } clientMutationId
} }"""


class _PaginationCountChanged(WriterError):
    """Internal, independently validated count guard; only restartable failure."""


def validate_config(config):
    required = {"enabled","project","target","limits"}
    require(type(config) is dict and set(config) in (required, required | {"verification"}), "invalid writer config")
    require(type(config["enabled"]) is bool, "enabled must be an explicit boolean")
    project, target, limits = config["project"], config["target"], config["limits"]
    require(type(project) is dict and set(project)=={"id","owner","owner_type","number"}, "invalid Project scope")
    require(project["owner_type"]=="user", "this pilot writer supports user-owned Projects only")
    require(type(target) is dict and set(target)=={"id","repository","number","head_sha"}, "invalid target scope")
    normalize({"complete":True,"project":dict(project,public=False,closed=False,fields=[]),
               "target":dict(target,state="OPEN"),"items":[]})
    require(type(limits) is dict and set(limits)=={"max_calls","rate_floor","max_pages","page_size"}, "invalid read limits")
    for key, low, high in (("max_calls",1,100),("rate_floor",100,5000),("max_pages",1,100),("page_size",1,100)):
        require(type(limits[key]) is int and low<=limits[key]<=high, "unsafe read limit")
    verification = config.get("verification", {"max_attempts":1,"max_seconds":30,"max_calls":10})
    require(type(verification) is dict and set(verification)=={"max_attempts","max_seconds","max_calls"}, "invalid verification limits")
    for key, upper in (("max_attempts",5),("max_seconds",120),("max_calls",30)):
        require(type(verification[key]) is int and 1<=verification[key]<=upper, "unsafe verification limit")
    require(verification["max_attempts"]==1 or limits["rate_floor"]>=200, "stabilization requires rate floor at least 200")
    return copy.deepcopy(config)


def value(node):
    require(type(node) is dict, "unreadable field value")
    typename=node.get("__typename", "")
    prefix="ProjectV2ItemField"
    require(typename.startswith(prefix) and typename.endswith("Value"), "unknown populated field value")
    kind=typename[len(prefix):-5]
    payload={k:v for k,v in node.items() if k not in ("__typename","field")}
    scalars={"Text":{"text"},"SingleSelect":{"optionId","name"},"Number":{"number"},"Date":{"date"},
             "Iteration":{"iterationId","title","startDate","duration"},"Repository":{"repository"},"Milestone":{"milestone"}}
    collections={"Label":"labels","User":"users","PullRequest":"pullRequests","Reviewer":"reviewers"}
    if kind in collections:
        key=collections[kind]
        require(set(payload)=={key}, "missing populated collection")
        nodes=whole_connection(payload[key])
        require(all(identifier(n.get("id")) for n in nodes), "unreadable field relation")
        require(len({n["id"] for n in nodes})==len(nodes), "duplicate field relation")
        payload[key]=sorted(nodes,key=lambda n:n["id"])
    else:
        require(kind in scalars and set(payload)==scalars[kind], "unsupported or incomplete populated field")
        if kind in ("Repository","Milestone"):
            relation=payload["repository" if kind=="Repository" else "milestone"]
            expected={"id","nameWithOwner"} if kind=="Repository" else {"id","title","state","dueOn"}
            require(type(relation) is dict and set(relation)==expected and identifier(relation.get("id")), "redacted or malformed populated relation")
            if kind=="Repository":
                require(type(relation["nameWithOwner"]) is str and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",relation["nameWithOwner"]), "repository relation unreadable")
            else:
                require(type(relation["title"]) is str and relation["state"] in ("OPEN","CLOSED")
                        and (relation["dueOn"] is None or type(relation["dueOn"]) is str), "milestone relation unreadable")
    require(type(node.get("field")) is dict and identifier(node["field"].get("id")), "field identity unavailable")
    return {"field_id":node["field"]["id"],"kind":kind,"value":payload}


class Backend:
    def __init__(self, config, transport=None, *, armed=False, monotonic=None):
        self.config=validate_config(config)
        self.transport=transport or self._default_transport
        self._monotonic = monotonic or time.monotonic
        self._verification = None
        self._verification_window = None
        self.verification_summary = None
        self.client=GhClient(self.config["limits"],self._read_transport)
        self.armed=armed is True and self.config["enabled"] is True
        self.attempted=False
        self.metrics={"read_calls":0,"read_points":0,"mutation_attempts":0}
        self.read_evidence = {}
        self._transport_failure = None

    def _default_transport(self, document, variables):
        timeout = 45
        if self._verification is not None:
            self._guard_time()
            timeout = min(timeout, self._verification["deadline"]-self._monotonic())
        return gh_transport(document, variables, timeout=timeout)

    def _guard_time(self):
        if self._verification is not None:
            require(self._monotonic() < self._verification["deadline"], "verification elapsed budget exhausted")

    def _guard_read(self):
        self._guard_time()
        if self._verification is not None:
            require(self.metrics["read_calls"]-self._verification["start_calls"] < self._verification["max_calls"],
                    "verification call budget exhausted")

    def _check_expected_item(self, item):
        if self._verification is None:
            return
        expected = self._verification
        original = expected["originals"].get(item["id"])
        comparable = dict(item, values=sorted(item["values"],key=lambda v:v["field_id"]))
        if original is not None:
            require(comparable==original, "original item/field state changed")
        else:
            require(item["content_id"]==expected["before"]["target"]["id"], "unrelated Project membership changed")
            require(item["id"]==expected["item_id"], "target response item differs")
            require(not item["archived"], "target archived after acknowledgment")

    def read_for_verification(self, before, item_id, record):
        """Only count inconsistency can restart; every attempt starts a fresh read."""
        policy = self.config.get("verification", {"max_attempts":1,"max_seconds":30,"max_calls":10})
        start = self._monotonic()
        self._verification_window = {"start":start,"deadline":start+policy["max_seconds"]}
        self._verification = dict(policy, deadline=start+policy["max_seconds"], start_calls=self.metrics["read_calls"],
                                  before=before, originals={i["id"]:i for i in before["items"]}, item_id=item_id)
        self.verification_summary = dict(policy, attempts=0, elapsed_milliseconds=0, read_calls=0)
        def persist(data):
            try:
                record(data)
            except Exception:
                self.read_evidence["failure_code"] = "verification_receipt_failed"
                raise WriterError("verification evidence persistence failed") from None
        try:
            for attempt in range(1,policy["max_attempts"]+1):
                self.verification_summary["attempts"] = attempt
                try:
                    snapshot = self.read()
                    self._guard_time()
                except Exception as error:
                    code = self.read_evidence.get("failure_code", error_code(error))
                    persist({"attempt":attempt,"outcome":"failed", "diagnostic":{
                        "code":code,"phase":"readback","read_evidence":safe_evidence(self.read_evidence)}})
                    if type(error) is not _PaginationCountChanged or attempt==policy["max_attempts"]:
                        raise
                    # The next fresh read checks shared budgets before its first
                    # query and records the terminal guard if no budget remains.
                    continue
                persist({"attempt":attempt,"outcome":"complete_read", "read_evidence":safe_evidence(self.read_evidence)})
                self._guard_time()
                return snapshot
        finally:
            self.verification_summary.update(elapsed_milliseconds=max(0,int((self._monotonic()-start)*1000)),
                                             read_calls=self.metrics["read_calls"]-self._verification["start_calls"])
            self._verification = None

    def finish_verification(self):
        """Check the retained deadline after policy validation, before acceptance."""
        if self._verification_window is not None:
            elapsed = self._monotonic()-self._verification_window["start"]
            self.verification_summary["elapsed_milliseconds"] = max(0,int(elapsed*1000))
            require(self._monotonic() < self._verification_window["deadline"], "verification elapsed budget exhausted")

    def _read_transport(self, document, variables):
        self.metrics["read_calls"]+=1
        page = {"call_index": self.metrics["read_calls"]}
        self.read_evidence["pages"].append(page)
        try:
            response=self.transport(document,variables)
        except Exception as error:
            self._transport_failure = error_code(error)
            raise
        data=response.get("data") if type(response) is dict else None
        rate=data.get("rateLimit") if type(data) is dict else None
        if type(rate) is dict and type(rate.get("cost")) is int:
            self.metrics["read_points"]+=rate["cost"]
        if type(rate) is dict:
            for key in ("cost", "remaining"):
                if type(rate.get(key)) is int: page[key] = rate[key]
        if type(data) is dict and type(data.get("project")) is dict:
            project = data["project"]
            items = project.get("items")
            if type(items) is dict:
                if type(items.get("nodes")) is list: page["node_count"] = len(items["nodes"])
                if type(items.get("totalCount")) is int: page["total_count"] = items["totalCount"]
                if type(items.get("pageInfo")) is dict:
                    page["has_next_page"] = items["pageInfo"].get("hasNextPage")
            for key, value in (("items_sha256", items), ("fields_sha256", project.get("fields")), ("target_sha256", data.get("target"))):
                try:
                    page[key] = sha(value)
                except (TypeError, ValueError):
                    pass
        return response

    def read(self):
        self._transport_failure = None
        self.read_evidence = dict(self.config["limits"], pages=[], started_at_unix=int(time.time()),
                                  read_calls_before=self.metrics["read_calls"], points_before=self.metrics["read_points"])
        try:
            return self._read()
        except Exception as error:
            code = error_code(error)
            if code == "transport_or_json_error" and self._transport_failure in ("transport_timeout", "verification_time_exhausted", "response_bound_exceeded"):
                code = self._transport_failure
            self.read_evidence["failure_code"] = code
            raise
        finally:
            self.read_evidence.update(finished_at_unix=int(time.time()), read_calls_after=self.metrics["read_calls"],
                                      points_after=self.metrics["read_points"])
            self.read_evidence = safe_evidence(self.read_evidence)

    def _read(self):
        cfg=self.config; cursor=None; cursors=set(); items=[]; metadata=None; total=None
        item_ids, content_ids = set(), set()
        for _ in range(cfg["limits"]["max_pages"]):
            self._guard_read()
            data=self.client.query(READ,{"project":cfg["project"]["id"],"target":cfg["target"]["id"],
                                        "cursor":cursor,"size":cfg["limits"]["page_size"]})
            self._guard_time()
            p,t=data.get("project"),data.get("target")
            require(type(p) is dict and type(t) is dict and type(p.get("owner")) is dict, "Project/PR unavailable")
            require(data.get("viewer",{}).get("login")==cfg["project"]["owner"], "unexpected gh identity; no credential changes attempted")
            expected_owner="User" if cfg["project"]["owner_type"]=="user" else "Organization"
            require(p["owner"].get("__typename")==expected_owner and p["owner"].get("login")==cfg["project"]["owner"], "Project owner mismatch")
            require(p.get("id")==cfg["project"]["id"] and p.get("number")==cfg["project"]["number"], "Project identity mismatch")
            target={"id":t.get("id"),"repository":(t.get("repository") or {}).get("nameWithOwner"),
                    "number":t.get("number"),"head_sha":t.get("headRefOid"),"state":t.get("state")}
            require(t.get("__typename")=="PullRequest" and target==dict(cfg["target"],state="OPEN"), "target identity/head/state mismatch")
            fields=whole_connection(p.get("fields"))
            require(all(f.get("__typename") in ("ProjectV2Field","ProjectV2SingleSelectField","ProjectV2IterationField") for f in fields), "unsupported Project field definition")
            fields=sorted(fields,key=lambda f:f["id"])
            for f in fields:
                if "options" in f: f["options"]=sorted(f["options"],key=lambda o:o["id"])
                if "configuration" in f:
                    for key in ("iterations","completedIterations"):
                        f["configuration"][key]=sorted(f["configuration"][key],key=lambda o:o["id"])
            project=dict(cfg["project"],public=p.get("public"),closed=p.get("closed"),fields=fields)
            observed={"project":project,"target":target}
            if self._verification is not None:
                require(project==self._verification["before"]["project"] and target==self._verification["before"]["target"],
                        "Project or target state changed")
            require(metadata is None or metadata==observed, "Project/target changed during pagination")
            metadata=observed
            batch,count,page=connection_page(p.get("items"))
            for node in batch:
                content=node.get("content")
                require(type(content) is dict, "redacted Project content")
                item={"id":node.get("id"),"content_id":content.get("id"),"kind":content.get("__typename"),
                      "archived":node.get("isArchived"),"values":[value(v) for v in whole_connection(node.get("fieldValues"))]}
                item = normalize_items([item], {f["id"] for f in fields})[0]
                self._check_expected_item(item)
                require(item["id"] not in item_ids and item["content_id"] not in content_ids, "duplicate item/content identity")
                item_ids.add(item["id"]); content_ids.add(item["content_id"])
                items.append(item)
            if page["hasNextPage"]:
                require(page["endCursor"] not in cursors, "pagination cursor repeated")
            require(len(items)<=count, "inconsistent item count")
            if not page["hasNextPage"]:
                require(len(items)==count, "incomplete Project item read")
            if total is not None and total!=count:
                raise _PaginationCountChanged("membership count changed during pagination")
            total=count
            if not page["hasNextPage"]:
                snapshot = normalize(dict(metadata,items=items,complete=True))
                self._guard_time()
                return snapshot
            cursor=page["endCursor"]
            cursors.add(cursor)
        raise WriterError("Project page budget exhausted")

    def add(self, project_id, content_id, operation_id):
        require(self.armed and not self.attempted, "transport disabled or operation already attempted")
        require(project_id==self.config["project"]["id"] and content_id==self.config["target"]["id"]
                and type(operation_id) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,80}",operation_id), "mutation scope mismatch")
        require(self.client.remaining is not None and self.client.remaining>=self.config["limits"]["rate_floor"], "complete preflight read required")
        self.attempted=True
        self.metrics["mutation_attempts"]+=1
        # No retry, document injection, REST fallback, or raw transport error output.
        try:
            response=self.transport(ADD_ONE,{"project":project_id,"content":content_id,"operation":operation_id})
            require(type(response) is dict and not response.get("errors"), "mutation response uncertain")
            result=response["data"]["addProjectV2ItemById"]
            require(result["clientMutationId"]==operation_id and identifier(result["item"]["id"]), "mutation acknowledgment mismatch")
            return result["item"]["id"]
        except Exception:
            raise WriterError("add outcome uncertain; use read-only recovery, never resend") from None
