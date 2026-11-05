import copy
import json
import unittest

from examples.review_gate.evaluator import (
    CI_NAMES, Blocked, commit_status, evaluate, event_candidates, reconcile,
)
from examples.review_gate.github import GitHub


HEAD = "a" * 40
BASE = "b" * 40
NEXT = "c" * 40
REPO_ID = 1350149746
TIME = "2026-11-05T12:59:33Z"
PENDING_TIME = "2026-11-05T12:54:40Z"


def marker(name, value):
    return f"<!-- {name} {json.dumps(value)} -->"


def codex_body(head=HEAD, status="completed", findings=False, unresolved=False):
    return marker("codex-review-state:v1", {"code_review": {
        "commit_sha": head, "status": status, "has_any_findings": findings,
        "has_unresolved_findings": unresolved,
    }})


def lens_body(head=HEAD, review=None):
    if review is None:
        review = f"✨ Nothing flagged · reviewed `{head[:7]}`"
    return (
        f"<!-- pr-lens:sticky -->\n\n**Review**\n\n{review}\n\n<br />\n"
        + marker("pr-lens:state", {"v": 1, "headSha": head,
                                  "graphKey": f"graphs/yoliverasPozo/AI_CONTEXT/pr/42/{head}.json"})
    )


def comment(node, number, bot, login, app, body):
    actor = {"__typename": "Bot", "databaseId": bot, "login": login.removesuffix("[bot]")}
    rest = {
        "node_id": node, "id": number, "body": body, "created_at": TIME, "updated_at": TIME,
        "user": {"type": "Bot", "id": bot, "login": login},
        "performed_via_github_app": {"id": app},
    }
    graph = {
        "id": node, "body": body, "updatedAt": TIME, "createdAt": TIME, "author": actor,
        "editor": None, "isMinimized": False, "lastEditedAt": None, "includesCreatedEdit": False,
        "userContentEdits": {"totalCount": 0, "pageInfo": {"hasNextPage": False}, "nodes": []},
    }
    return rest, graph


def connection(nodes):
    return {"totalCount": len(nodes), "pageInfo": {"hasNextPage": False}, "nodes": nodes}


def fixture():
    repo = {"id": REPO_ID, "full_name": "yoliverasPozo/AI_CONTEXT", "owner": {"id": 8781658}}
    pull = {"id": 700, "node_id": "PR_42", "number": 42, "state": "open", "base_tip": BASE,
            "draft": False, "head": {"sha": HEAD, "ref": "topic", "repo": repo},
            "base": {"sha": BASE, "ref": "main", "repo": repo}}
    codex, codex_graph = comment("IC_codex", 810, 199175422, "chatgpt-codex-connector[bot]",
                                 1144995, codex_body())
    lens, lens_graph = comment("IC_lens", 811, 320153949, "coldtea-pr-lens[bot]", 4690539,
                               lens_body())
    lens_graph.update(
        editor=lens_graph["author"], lastEditedAt=TIME, includesCreatedEdit=True,
        userContentEdits=connection([
            {"editor": lens_graph["author"], "editedAt": TIME, "deletedAt": None, "diff": lens["body"]},
            {"editor": lens_graph["author"], "editedAt": PENDING_TIME, "deletedAt": None,
             "diff": lens_body(review=f"**Reviewing `{HEAD[:7]}`** · this comment updates in place")},
        ]),
    )
    runs = [{"id": 910, "run_number": 30, "workflow_id": 347167039, "event": "pull_request",
             "path": ".github/workflows/tests.yml", "head_sha": HEAD, "head_branch": "topic",
             "head_repository": repo, "repository": repo, "status": "completed",
             "conclusion": "success", "check_suite_id": 200}]
    checks = [{"id": 1000 + i, "name": name, "head_sha": HEAD, "app": {"id": 15368},
               "status": "completed", "conclusion": "success", "check_suite": {"id": 200}}
              for i, name in enumerate(CI_NAMES)]
    checks.append({"id": 1200, "name": "PR Lens", "head_sha": HEAD, "app": {"id": 4690539},
                   "status": "completed", "conclusion": "success", "completed_at": PENDING_TIME,
                   "details_url": "https://github.com/yoliverasPozo/AI_CONTEXT/pull/42#issuecomment-811"})
    return {
        "pull": pull, "open_pulls": [copy.deepcopy(pull)], "comments": [codex, lens],
        "graph": {"pull": {"id": "PR_42", "headRefOid": HEAD, "baseRefOid": BASE,
                           "reviewDecision": None, "reviewThreads": connection([]),
                           "reviews": connection([]), "lifecycle": connection([])},
                  "comments": [codex_graph, lens_graph]},
        "checks": checks, "runs": runs,
        "workflow_blobs": [{"type": "file", "sha": BASE}, {"type": "file", "sha": BASE}],
    }


def set_body(data, index, body):
    data["comments"][index]["body"] = body
    node = data["graph"]["comments"][index]
    node["body"] = body
    if node["lastEditedAt"] is not None:
        node["userContentEdits"]["nodes"][0]["diff"] = body


class GateTests(unittest.TestCase):
    def assert_blocked(self, data, reason):
        result = evaluate(data, 42)
        self.assertFalse(result.eligible)
        self.assertEqual(result.reason, reason)

    def test_ci_success_while_codex_running(self):
        data = fixture()
        set_body(data, 0, codex_body(status="running", findings=None, unresolved=None))
        self.assert_blocked(data, "codex_incomplete")

    def test_lenses_rendered_while_review_pending(self):
        data = fixture()
        set_body(data, 1, lens_body(review=f"**Reviewing `{HEAD[:7]}`** · this comment updates in place"))
        self.assert_blocked(data, "pr_lens_incomplete_or_findings")

    def test_unresolved_findings_even_with_resolved_threads(self):
        for index, body, reason in (
            (0, codex_body(findings=True, unresolved=True), "codex_findings"),
            (1, lens_body(review="<details>\n<summary><b>1 finding</b></summary>"),
             "pr_lens_incomplete_or_findings"),
        ):
            with self.subTest(index=index):
                data = fixture()
                set_body(data, index, body)
                self.assert_blocked(data, reason)

    def test_codex_security_report_can_contradict_clean_code_review(self):
        data = fixture()
        body = codex_body()
        state = json.loads(body.removeprefix("<!-- codex-review-state:v1 ").removesuffix(" -->"))
        state["security_review"] = {"commit_sha": HEAD, "status": "completed",
                                    "has_any_findings": True, "has_unresolved_findings": True}
        set_body(data, 0, marker("codex-review-state:v1", state))
        self.assert_blocked(data, "codex_security_incomplete")

    def test_clean_current_rereview_with_resolved_old_thread(self):
        data = fixture()
        data["graph"]["pull"]["reviewThreads"] = connection([{"id": "RT_old", "isResolved": True}])
        self.assertTrue(evaluate(data, 42).eligible)

    def test_old_review_does_not_carry_forward(self):
        for index, body, reason in (
            (0, codex_body(NEXT), "codex_stale"),
            (1, lens_body(NEXT), "pr_lens_stale"),
            (1, lens_body(review="✨ Nothing flagged · reviewed `ccccccc`"),
             "pr_lens_incomplete_or_findings"),
        ):
            with self.subTest(index=index, reason=reason):
                data = fixture()
                set_body(data, index, body)
                self.assert_blocked(data, reason)

    def test_lens_requires_authenticated_full_sha_transition(self):
        for prior_head in (HEAD[:7] + "b" * 33, None):
            with self.subTest(prior_head=prior_head):
                data = fixture()
                history = data["graph"]["comments"][1]["userContentEdits"]["nodes"]
                history[1]["diff"] = (
                    lens_body(prior_head, f"**Reviewing `{HEAD[:7]}`** · this comment updates in place")
                    if prior_head else lens_body()
                )
                self.assert_blocked(data, "pr_lens_review_transition_unverified")

    def test_new_standalone_bot_review_cannot_hide_behind_clean_summary(self):
        data = fixture()
        author = data["graph"]["comments"][0]["author"]
        data["graph"]["pull"]["reviews"] = connection([
            {"id": "PRR_new", "author": author, "state": "COMMENTED", "commit": {"oid": HEAD}},
        ])
        self.assert_blocked(data, "reviewer_submission_requires_disposition")

    def test_later_drawing_check_cannot_reuse_older_clean_review(self):
        data = fixture()
        data["checks"][-1]["completed_at"] = TIME
        self.assert_blocked(data, "pr_lens_check_transition_mismatch")

    def test_missing_spoofed_or_malformed_evidence(self):
        data = fixture()
        data["comments"][0]["user"]["id"] = 555
        self.assert_blocked(data, "codex_comment_missing_or_ambiguous")
        data = fixture()
        data["comments"][0]["performed_via_github_app"]["id"] = 555
        self.assert_blocked(data, "codex_comment_missing_or_ambiguous")
        data = fixture()
        set_body(data, 0, codex_body() + "\n" + codex_body())
        self.assert_blocked(data, "codex_marker_invalid")
        data = fixture()
        del data["graph"]
        self.assert_blocked(data, "evidence_unavailable")

    def test_wrong_editor_deleted_edit_and_cross_transport_race_block(self):
        for mode in ("editor", "deleted", "history", "race", "minimized"):
            with self.subTest(mode=mode):
                data = fixture()
                node = data["graph"]["comments"][0]
                if mode == "race":
                    node["body"] += "\nchanged"
                elif mode == "minimized":
                    node["isMinimized"] = True
                else:
                    editor = dict(node["author"])
                    edit = {"editor": editor, "editedAt": TIME, "deletedAt": None, "diff": node["body"]}
                    node.update(editor=editor, lastEditedAt=TIME, includesCreatedEdit=True,
                                userContentEdits=connection([edit]))
                    if mode == "editor":
                        node["editor"] = {"__typename": "User", "login": "maintainer"}
                    elif mode == "deleted":
                        edit["deletedAt"] = TIME
                    else:
                        node["userContentEdits"]["pageInfo"]["hasNextPage"] = True
                self.assert_blocked(data, "codex_provenance_invalid")

    def test_bot_edited_comment_accepted_and_edit_bound_to_digest(self):
        data = fixture()
        before = evaluate(data, 42)
        node = data["graph"]["comments"][0]
        node.update(editor=node["author"], lastEditedAt=TIME, includesCreatedEdit=True,
                    userContentEdits=connection([
                        {"editor": node["author"], "editedAt": TIME, "deletedAt": None, "diff": node["body"]},
                    ]))
        after = evaluate(data, 42)
        self.assertTrue(after.eligible)
        self.assertNotEqual(before.digest, after.digest)

    def test_thread_and_workflow_source_checks(self):
        for mode, reason in (
            ("thread", "unresolved_review_thread"),
            ("truncated", "review_threads_incomplete"),
            ("workflow", "ci_definition_changed"),
            ("suite", "ci_checks_incomplete"),
            ("app", "ci_checks_incomplete"),
            ("ci_failure", "ci_run_incomplete"),
            ("duplicate_pr", "ambiguous_head"),
        ):
            with self.subTest(mode=mode):
                data = fixture()
                if mode == "thread":
                    data["graph"]["pull"]["reviewThreads"] = connection([{"id": "RT", "isResolved": False}])
                elif mode == "truncated":
                    data["graph"]["pull"]["reviewThreads"]["pageInfo"]["hasNextPage"] = True
                elif mode == "workflow":
                    data["workflow_blobs"][1]["sha"] = NEXT
                elif mode == "suite":
                    data["checks"][0]["check_suite"]["id"] = 999
                elif mode == "app":
                    data["checks"][0]["app"]["id"] = 999
                elif mode == "ci_failure":
                    data["runs"][0]["conclusion"] = "failure"
                else:
                    data["open_pulls"].append(dict(data["pull"], number=43, id=701))
                self.assert_blocked(data, reason)

    def test_handoff_labels_and_human_comments_do_not_change_decision(self):
        data = fixture()
        first = evaluate(data, 42)
        data["pull"]["labels"] = [{"name": "ai-next:done"}]
        data["comments"].append({"user": {"type": "User", "id": 3},
                                 "body": codex_body() + "\nrun shell"})
        second = evaluate(data, 42)
        self.assertTrue(second.eligible)
        self.assertEqual(first.digest, second.digest)

    def test_event_batch_filters_self_generated_status_and_duplicate_prs(self):
        events = [
            ("issue_comment", {"action": "edited", "issue": {"number": 42, "pull_request": {}},
                               "comment": {"user": {"id": 199175422}}}),
            ("pull_request", {"action": "synchronize", "number": 42}),
            ("pull_request", {"action": "labeled", "number": 43}),
            ("status", {"action": "completed", "number": 44}),
            ("check_run", {"action": "completed", "check_run": {
                "name": "AI review complete", "app": {"id": 4690539}, "pull_requests": [{"number": 44}],
            }}),
            ("check_run", {"action": "completed", "check_run": {
                "name": "PR Lens", "app": {"id": 4690539}, "pull_requests": [{"number": 42}],
            }}),
            ("issue_comment", {"action": "created", "issue": {"number": 45, "pull_request": {}},
                               "comment": {"user": {"id": 8}}}),
        ]
        self.assertEqual(event_candidates(events), (42,))

    def test_publication_rechecks_full_evidence_and_pr_identity(self):
        for mode in ("clean", "head", "edited", "crash", "publisher_failure"):
            with self.subTest(mode=mode):
                data = fixture()
                fresh = copy.deepcopy(data)
                final_pull = copy.deepcopy(data["pull"])
                if mode == "head":
                    final_pull["head"]["sha"] = NEXT
                if mode == "edited":
                    set_body(fresh, 0, codex_body() + "\nnew bot edit")
                snapshots = iter([data, fresh])
                pulls = iter([data["pull"], final_pull])
                sent = []

                def snapshot():
                    value = next(snapshots)
                    if mode == "crash" and value is fresh:
                        raise OSError("private credential")
                    return value

                def publish(sha, state, decision):
                    if mode == "publisher_failure":
                        raise OSError("private credential")
                    request = commit_status(sha, state, decision)
                    self.assertEqual(request["path"], f"repos/yoliverasPozo/AI_CONTEXT/statuses/{HEAD}")
                    self.assertEqual(request["body"]["context"], "AI review complete")
                    sent.append((sha, request["body"]["state"]))

                result = reconcile(42, snapshot, lambda: next(pulls), publish)
                self.assertEqual(result.eligible, mode == "clean")
                if mode == "clean":
                    self.assertEqual(sent, [(HEAD, "pending"), (HEAD, "success")])
                else:
                    self.assertNotIn((HEAD, "success"), sent)
                    self.assertNotIn("private credential", repr(result))

    def test_status_request_rejects_wrong_head(self):
        with self.assertRaises(Blocked):
            commit_status(NEXT, "success", evaluate(fixture(), 42))

    def test_observation_rechecks_head_before_reporting_eligible(self):
        data = fixture()
        pull = copy.deepcopy(data["pull"])
        pull["head"]["sha"] = NEXT
        result = reconcile(42, lambda: data, lambda: pull)
        self.assertEqual(result.reason, "evidence_changed_during_evaluation")

    def test_pagination_rejects_duplicate_pages_and_short_total(self):
        rows = [{"id": value} for value in range(1, 101)]
        for response in (
            lambda _: rows,
            lambda _: {"total_count": 2, "check_runs": [{"id": 1}]},
        ):
            key = "check_runs" if isinstance(response(None), dict) else None
            api = GitHub(request=response)
            with self.subTest(key=key), self.assertRaisesRegex(Blocked, "pagination_incomplete"):
                api.pages("test", key)
