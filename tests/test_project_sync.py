"""Behavior tests for the optional plan-only example; no live services required."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from examples.project_sync.planner import PlanError, plan, validate_config
from examples.project_sync.collector import GhClient, collect


HEAD = "a" * 40
BLOB = "b" * 40


def config():
    return {"project": {"owner": "example", "owner_type": "user", "number": 1},
            "repositories": [{"name": "example/widget", "issues": [4],
                              "handoffs": {"2": "docs/sessions/task.md"}}],
            "actor_field": "Next actor",
            "roles": {"work": {"owner": "Work implementer", "value": "Work"},
                      "codex": {"owner": "Codex reviewer", "value": "Codex"}}}


def pr(number=2, node_id="PR_2", **changes):
    value = {"id": node_id, "kind": "PullRequest", "repository": "example/widget",
             "number": number, "state": "OPEN", "merged": False, "head_sha": HEAD,
             "body": "<!-- ai-context-next: work -->", "labels": ["ai-next:work"]}
    value.update(changes)
    return value


def snapshot(items=None, prs=None, issues=None, handoffs=None):
    return {"schema_version": 1, "complete": True,
            "project": {"owner": "example", "owner_type": "user", "number": 1,
                        "id": "PROJECT", "items": items or []},
            "pull_requests": prs if prs is not None else [pr()],
            "issues": issues or [], "handoffs": handoffs or []}


def item(content=None, archived=False, fields=None):
    return {"id": "ITEM_2", "archived": archived, "content": content or pr(),
            "fields": fields or {}}


def handoff(**changes):
    value = {"repository": "example/widget", "number": 2,
             "path": "docs/sessions/task.md", "head_sha": HEAD,
             "observed_head_sha": HEAD, "blob_sha": BLOB,
             "text": "# Session\n\n## Coordination\nTask ID: task\nStatus: ready\n"
                     "Next owner: Work implementer\nRepository: example/widget\n\n## Goal\nReview."}
    value.update(changes)
    return value


class PlannerTests(unittest.TestCase):
    def test_missing_open_pr_and_explicit_issue_are_additions(self):
        issue = {"id": "ISSUE_4", "kind": "Issue", "repository": "example/widget",
                 "number": 4, "state": "OPEN"}
        result = plan(config(), snapshot(issues=[issue]))
        self.assertEqual([x["content_id"] for x in result["additions"]], ["ISSUE_4", "PR_2"])
        self.assertEqual(result["field_proposals"], [])
        self.assertEqual(result["mode"], "plan-only")

    def test_existing_and_archived_identities_never_add_again(self):
        for archived in [False, True]:
            with self.subTest(archived=archived):
                result = plan(config(), snapshot(items=[item(archived=archived)]))
                self.assertEqual(result["additions"], [])

    def test_replaying_reviewed_additions_and_actor_values_is_idempotent(self):
        source = snapshot(handoffs=[handoff()])
        first = plan(config(), source)
        self.assertEqual(len(first["additions"]), 1)
        source["project"]["items"] = [item(fields={"Next actor": "Work"})]
        replay = plan(config(), source, first["proposed_cursor"])
        self.assertEqual(replay["additions"], [])
        self.assertEqual(replay["field_proposals"], [])
        self.assertEqual(replay["notification_proposals"], [])

    def test_duplicate_content_and_duplicate_items_refuse_plan(self):
        for duplicate in [dict(item(), id="ITEM_OTHER"), item()]:
            with self.assertRaises(PlanError):
                plan(config(), snapshot(items=[item(), duplicate]))

    def test_nonallowlisted_candidates_and_unconfigured_issues_are_not_imported(self):
        other = pr(9, "OTHER", repository="outside/repo")
        issue = {"id": "ISSUE_9", "kind": "Issue", "repository": "example/widget",
                 "number": 9, "state": "OPEN"}
        result = plan(config(), snapshot(prs=[other], issues=[issue]))
        self.assertEqual(result["additions"], [])

    def test_manual_actor_and_gate_fields_survive(self):
        source = snapshot(items=[item(fields={"Next actor": "Maintainer",
                              "Approval gate": "Production hold", "Status": "Blocked"})],
                          handoffs=[handoff()])
        before = copy.deepcopy(source)
        result = plan(config(), source)
        self.assertEqual(result["field_proposals"], [])
        self.assertEqual(source, before)

    def test_matching_current_head_journal_fills_only_blank_actor(self):
        result = plan(config(), snapshot(items=[item()], handoffs=[handoff()]))
        self.assertEqual(result["field_proposals"], [{"item_id": "ITEM_2",
            "field": "Next actor", "before": None, "after": "Work",
            "head_sha": HEAD, "handoff_blob_sha": BLOB}])
        self.assertEqual(len(result["notification_proposals"]), 1)

    def test_stale_head_conflict_duplicate_metadata_and_nonready_stay_unknown(self):
        cases = [handoff(observed_head_sha="c" * 40), handoff(head_sha="c" * 40),
                 handoff(text=handoff()["text"].replace("Work implementer", "Codex reviewer")),
                 handoff(text=handoff()["text"].replace("Status: ready", "Status: active")),
                 handoff(text=handoff()["text"].replace("Status: ready", "Status: ready\nStatus: ready")),
                 handoff(blob_sha="unknown")]
        for record in cases:
            with self.subTest(record=record):
                result = plan(config(), snapshot(items=[item()], handoffs=[record]))
                self.assertEqual(result["field_proposals"], [])
                self.assertEqual(result["notification_proposals"], [])
                self.assertTrue(result["diagnostics"])

    def test_duplicate_markers_labels_and_unconfigured_path_fail_admission(self):
        for changes in [{"body": pr()["body"] * 2},
                        {"body": pr()["body"] + "<!-- ai-context-next: unknown -->"},
                        {"labels": ["ai-next:work", "ai-next:codex"]},
                        {"labels": []}]:
            result = plan(config(), snapshot(items=[item()], prs=[pr(**changes)], handoffs=[handoff()]))
            self.assertEqual(result["field_proposals"], [])
        result = plan(config(), snapshot(items=[item()], handoffs=[handoff(path="unexpected.md")]))
        self.assertEqual(result["field_proposals"], [])

    def test_malformed_metadata_cannot_hide_conflicting_owner(self):
        record = handoff(text=handoff()["text"].replace("Next owner: Work implementer",
            "Next owner: Work implementer\n Next owner: Different owner"))
        result = plan(config(), snapshot(items=[item()], handoffs=[record]))
        self.assertEqual(result["field_proposals"], [])

    def test_quoted_fenced_example_cannot_become_handoff_authority(self):
        for fence in ["```", "````", "~~~"]:
            with self.subTest(fence=fence):
                record = handoff(text=fence + "markdown\n" + handoff()["text"] + "\n" + fence)
                result = plan(config(), snapshot(items=[item()], handoffs=[record]))
                self.assertEqual(result["field_proposals"], [])
                self.assertEqual(result["notification_proposals"], [])

    def test_code_fences_outside_live_coordination_are_allowed(self):
        text = "# Journal\n\n```markdown\n## Coordination\nStatus: active\n```\n\n" + handoff()["text"]
        result = plan(config(), snapshot(items=[item()], handoffs=[handoff(text=text)]))
        self.assertEqual(len(result["field_proposals"]), 1)

    def test_projection_cannot_target_reserved_fields(self):
        for field in ["Approval gate", "Status", "Handoff state", "Workstream", "Repository", "next actor"]:
            with self.subTest(field=field), self.assertRaises(PlanError):
                changed = config(); changed["actor_field"] = field
                plan(changed, snapshot(items=[item()], handoffs=[handoff()]))

    def test_archived_ready_handoff_is_not_queued(self):
        result = plan(config(), snapshot(items=[item(archived=True)], handoffs=[handoff()]))
        self.assertEqual(result["field_proposals"], [])
        self.assertEqual(result["notification_proposals"], [])

    def test_closed_and_merged_tracked_prs_only_suggest_terminal_state(self):
        closed = pr(state="CLOSED", merged=True)
        result = plan(config(), snapshot(items=[item(content=closed,
            fields={"Status": "Blocked", "Approval gate": "Owner decision"})], prs=[closed]))
        self.assertEqual(result["additions"], [])
        self.assertEqual(result["field_proposals"], [])
        self.assertEqual(result["terminal_suggestions"][0]["lifecycle"], "merged")
        self.assertEqual(result["terminal_suggestions"][0]["preserved_fields"]["Status"], "Blocked")

    def test_notification_cursor_is_proposed_and_deduplicates_by_revision(self):
        source = snapshot(items=[item()], handoffs=[handoff()])
        first = plan(config(), source)
        key = first["notification_proposals"][0]["key"]
        self.assertEqual(key, ["example/widget", 2, HEAD, "Work implementer", BLOB])
        second = plan(config(), source, {"schema_version": 1, "observed_keys": [key]})
        self.assertEqual(second["notification_proposals"], [])
        source["handoffs"][0]["blob_sha"] = "d" * 40
        third = plan(config(), source, first["proposed_cursor"])
        self.assertEqual(len(third["notification_proposals"]), 1)
        self.assertNotIn("delivered_keys", first["proposed_cursor"])

    def test_project_mismatch_incomplete_and_identity_conflicts_refuse_plan(self):
        bad = snapshot(); bad["project"]["number"] = 2
        incomplete = snapshot(); incomplete["complete"] = False
        conflict = snapshot(prs=[pr(), pr(3)])
        for source in [bad, incomplete, conflict]:
            with self.assertRaises(PlanError):
                plan(config(), source)

    def test_config_requires_explicit_valid_unique_allowlist_and_limits(self):
        bad_configs = []
        for mutate in [lambda c: c.update(repositories=[]),
                       lambda c: c["repositories"].append(c["repositories"][0]),
                       lambda c: c["repositories"][0].update(name="bad repo"),
                       lambda c: c.update(limits={"max_calls": 0}),
                       lambda c: c["repositories"][0].update(handoffs={"2": "../private.md"})]:
            c = config(); mutate(c); bad_configs.append(c)
        for c in bad_configs:
            with self.assertRaises(PlanError):
                validate_config(c)


class CliTests(unittest.TestCase):
    def test_offline_cli_and_no_apply_capability(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "config.json").write_text(json.dumps(config()), encoding="utf-8")
            (directory / "snapshot.json").write_text(json.dumps(snapshot()), encoding="utf-8")
            args = [sys.executable, "-m", "examples.project_sync", "--config",
                    str(directory / "config.json"), "--snapshot", str(directory / "snapshot.json")]
            result = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["mode"], "plan-only")
            blocked = subprocess.run(args + ["--apply"], capture_output=True, text=True)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertEqual(sorted(p.name for p in directory.iterdir()), ["config.json", "snapshot.json"])


def connection(nodes, total=None, more=False, cursor=None):
    return {"nodes": nodes, "totalCount": len(nodes) if total is None else total,
            "pageInfo": {"hasNextPage": more, "endCursor": cursor}}


def graph_pr(**changes):
    value = {"__typename": "PullRequest", "id": "PR_2", "number": 2,
             "repository": {"nameWithOwner": "example/widget"}, "state": "OPEN",
             "merged": False, "headRefOid": HEAD, "body": "<!-- ai-context-next: work -->",
             "labels": connection([{"name": "ai-next:work"}])}
    value.update(changes)
    return value


def project_page(nodes, total=None, more=False, cursor=None):
    return {"owner": {"projectV2": {"id": "PROJECT",
        "fields": connection([{"id": "FIELD", "name": "Next actor", "dataType": "SINGLE_SELECT"}]),
        "items": connection(nodes, total, more, cursor)}}}


class GraphTransport:
    """External GraphQL boundary fixture; production collector remains real."""
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, document, variables):
        self.requests.append((document, variables.copy()))
        if not self.responses:
            raise AssertionError("Unexpected extra request")
        data = copy.deepcopy(self.responses.pop(0))
        if "errors" in data:
            return data
        rate = data.pop("_rate", {"remaining": 4900, "cost": 1})
        return {"data": dict(data, rateLimit=rate)}


def collector_config():
    value = config()
    value["repositories"][0]["issues"] = []
    value["repositories"][0]["handoffs"] = {}
    return validate_config(value)


class CollectorTests(unittest.TestCase):
    def test_collect_paginates_project_and_repository_with_archived_identities(self):
        archived = {"id": "ARCHIVED_ITEM", "isArchived": True,
            "content": {"__typename": "PullRequest", "id": "PR_2", "number": 2,
                        "repository": {"nameWithOwner": "example/widget"}},
            "fieldValues": connection([])}
        transport = GraphTransport([project_page([archived], 1),
            {"repository": {"pullRequests": connection([graph_pr()], 2, True, "PAGE2")}},
            {"repository": {"pullRequests": connection([graph_pr(id="PR_3", number=3)], 2)}}])
        c = collector_config()
        source = collect(c, GhClient(c["limits"], transport))
        self.assertTrue(source["complete"])
        self.assertTrue(source["project"]["items"][0]["archived"])
        self.assertEqual([p["number"] for p in source["pull_requests"]], [2, 3])
        result = plan(c, source)
        self.assertEqual([a["content_id"] for a in result["additions"]], ["PR_3"])
        self.assertIn("archivedStates: [ARCHIVED, NOT_ARCHIVED]", transport.requests[0][0])
        self.assertEqual(transport.requests[2][1]["cursor"], "PAGE2")

    def test_project_pages_complete_before_repo_reads(self):
        draft = {"id": "DRAFT_ITEM", "isArchived": False,
                 "content": {"__typename": "DraftIssue", "id": "DRAFT"},
                 "fieldValues": connection([])}
        transport = GraphTransport([project_page([], 1, True, "NEXT"), project_page([draft], 1),
            {"repository": {"pullRequests": connection([])}}])
        c = collector_config()
        source = collect(c, GhClient(c["limits"], transport))
        self.assertEqual(len(source["project"]["items"]), 1)
        self.assertEqual(transport.requests[1][1]["cursor"], "NEXT")

    def test_tracked_closed_pr_is_refreshed_even_when_open_list_empty(self):
        tracked = {"id": "ITEM", "isArchived": False,
                   "content": {"__typename": "PullRequest", "id": "PR_2", "number": 2,
                               "repository": {"nameWithOwner": "example/widget"}},
                   "fieldValues": connection([])}
        transport = GraphTransport([project_page([tracked]),
            {"repository": {"pullRequests": connection([])}},
            {"node": graph_pr(state="MERGED", merged=True)}])
        c = collector_config()
        result = plan(c, collect(c, GhClient(c["limits"], transport)))
        self.assertEqual(result["terminal_suggestions"][0]["lifecycle"], "merged")
        self.assertEqual(transport.requests[2][1], {"id": "PR_2"})

    def test_outside_project_content_does_not_expand_repository_reads(self):
        outside = {"id": "OUTSIDE_ITEM", "isArchived": False,
                   "content": {"__typename": "PullRequest", "id": "OUTSIDE_PR", "number": 9,
                               "repository": {"nameWithOwner": "outside/repo"}},
                   "fieldValues": connection([])}
        transport = GraphTransport([project_page([outside]),
            {"repository": {"pullRequests": connection([graph_pr()])}}])
        c = collector_config()
        result = plan(c, collect(c, GhClient(c["limits"], transport)))
        self.assertEqual([a["content_id"] for a in result["additions"]], ["PR_2"])
        self.assertEqual(len(transport.requests), 2)

    def test_configured_issue_and_exact_head_blob_are_read_and_rechecked(self):
        c = validate_config(config())
        issue = {"__typename": "Issue", "id": "ISSUE_4", "number": 4, "state": "OPEN",
                 "repository": {"nameWithOwner": "example/widget"}}
        transport = GraphTransport([project_page([]),
            {"repository": {"pullRequests": connection([graph_pr()])}},
            {"repository": {"issue": issue}},
            {"repository": {"object": {"__typename": "Blob", "oid": BLOB,
                "text": handoff()["text"], "isTruncated": False, "isBinary": False,
                "byteSize": len(handoff()["text"].encode())}}},
            {"node": graph_pr()}])
        result = plan(c, collect(c, GhClient(c["limits"], transport)))
        self.assertEqual(len(result["notification_proposals"]), 1)
        self.assertEqual(transport.requests[3][1]["expression"], HEAD + ":docs/sessions/task.md")
        self.assertEqual(transport.requests[2][1]["number"], 4)

    def test_stale_head_during_blob_read_does_not_admit_actor(self):
        c = collector_config(); c["repositories"][0]["handoffs"] = {"2": "docs/sessions/task.md"}
        transport = GraphTransport([project_page([]),
            {"repository": {"pullRequests": connection([graph_pr()])}},
            {"repository": {"object": {"__typename": "Blob", "oid": BLOB,
                "text": handoff()["text"], "isTruncated": False, "isBinary": False,
                "byteSize": len(handoff()["text"].encode())}}},
            {"node": graph_pr(headRefOid="c" * 40)}])
        result = plan(c, collect(c, GhClient(c["limits"], transport)))
        self.assertEqual(result["notification_proposals"], [])
        self.assertEqual(result["field_proposals"], [])

    def test_missing_truncated_pages_repeated_cursor_and_count_drift_abort(self):
        pages = [project_page([], 1), project_page([], 1, True, None),
                 project_page([], 1, True, "SAME")]
        for first in pages:
            responses = [first, project_page([], 1, True, "SAME")]
            c = collector_config()
            with self.assertRaises(PlanError):
                collect(c, GhClient(c["limits"], GraphTransport(responses)))
        first = project_page([], 1, True, "NEXT")
        with self.assertRaises(PlanError):
            collect(c, GhClient(c["limits"], GraphTransport([first, project_page([], 2)])))

    def test_nested_truncation_and_null_content_abort(self):
        for content, fields in [(None, connection([])),
                                ({"__typename": "DraftIssue", "id": "D"}, connection([], 101, True, "N"))]:
            tracked = {"id": "ITEM", "isArchived": False, "content": content, "fieldValues": fields}
            c = collector_config()
            with self.assertRaises(PlanError):
                collect(c, GhClient(c["limits"], GraphTransport([project_page([tracked])])))

    def test_graphql_errors_rate_floor_and_call_budget_abort_without_partial_plan(self):
        c = collector_config()
        error_cases = [{"errors": [{"message": "private server details"}]},
                       dict(project_page([]), _rate={"remaining": 99, "cost": 1}),
                       dict(project_page([]), _rate=None)]
        for response in error_cases:
            with self.assertRaises(PlanError) as caught:
                collect(c, GhClient(c["limits"], GraphTransport([response])))
            self.assertNotIn("private server details", str(caught.exception))
        c["limits"]["max_calls"] = 1
        transport = GraphTransport([project_page([])])
        with self.assertRaises(PlanError):
            collect(c, GhClient(c["limits"], transport))
        self.assertEqual(len(transport.requests), 1)

    def test_scope_failure_and_subprocess_failure_do_not_echo_credentials(self):
        def denied(document, variables):
            raise subprocess.CalledProcessError(1, "gh", stderr="token=SECRET read:project required")
        c = collector_config()
        with self.assertRaises(PlanError) as caught:
            collect(c, GhClient(c["limits"], denied))
        self.assertIn("read:project", str(caught.exception))
        self.assertNotIn("SECRET", str(caught.exception))

    def test_labels_truncated_and_missing_repo_fail_closed(self):
        c = collector_config()
        for repo in [None, {"pullRequests": connection([graph_pr(labels=connection([], 101, True, "N"))])}]:
            with self.assertRaises(PlanError):
                collect(c, GhClient(c["limits"], GraphTransport([project_page([]), {"repository": repo}])))

    def test_missing_field_identity_and_page_budget_abort(self):
        c = collector_config()
        broken = {"id": "ITEM", "isArchived": False,
                  "content": {"__typename": "DraftIssue", "id": "DRAFT"},
                  "fieldValues": connection([{"__typename": "ProjectV2ItemFieldSingleSelectValue",
                                               "name": "Maintainer"}])}
        with self.assertRaises(PlanError):
            collect(c, GhClient(c["limits"], GraphTransport([project_page([broken])])))
        c["limits"]["max_pages"] = 1
        with self.assertRaises(PlanError):
            collect(c, GhClient(c["limits"], GraphTransport([project_page([], 1, True, "NEXT")])))
