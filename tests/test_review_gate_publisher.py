import copy
import json
import unittest

from examples.review_gate.evaluator import evaluate, event_candidates
from examples.review_gate.github import GitHub
from examples.review_gate.publisher import SandboxPublisher
from tests.test_ai_review_gate import HEAD, NEXT, codex_body, comment, connection, fixture, set_body, lens_finding_body


APP = 501


def run(publisher, data, **kwargs):
    return publisher.run(data["pull"]["number"], lambda: data, lambda: data["pull"],
                         actor_app_id=APP, **kwargs)


def state(publisher):
    receipt = publisher.visible(HEAD)
    return receipt.request["body"]["state"] if receipt else None


def findings(data):
    set_body(data, 0, codex_body(findings=True, unresolved=True))


class PublisherTests(unittest.TestCase):
    def test_default_disabled_and_requires_dedicated_identity(self):
        data = fixture()
        self.assertEqual(run(SandboxPublisher(APP), data).reason, "sandbox_publisher_disabled")
        publisher = SandboxPublisher(APP, enabled=True)
        result = publisher.run(42, self.fail, self.fail, actor_app_id=15368)
        self.assertEqual(result.reason, "sandbox_publisher_identity_mismatch")
        self.assertIsNone(state(publisher))

    def test_pending_success_failure_and_pr_specific_receipt(self):
        publisher = SandboxPublisher(APP, enabled=True)
        data = fixture()
        observed = []

        def snapshot():
            observed.append(state(publisher))
            return data

        decision = publisher.run(42, snapshot, lambda: data["pull"], actor_app_id=APP)
        self.assertEqual(observed, ["pending", "pending"])
        receipt = publisher.confirmed_for(decision)
        self.assertEqual((receipt.app_id, receipt.scope["number"], receipt.scope["head"]), (APP, 42, HEAD))
        self.assertEqual(receipt.scope["base_tip"], data["pull"]["base_tip"])
        self.assertEqual(receipt.evidence["codex"], decision.evidence["codex"])
        self.assertEqual(state(publisher), "success")
        findings(data)
        self.assertEqual(run(publisher, data).reason, "codex_findings")
        self.assertEqual(state(publisher), "failure")
        self.assertIsNone(publisher.confirmed_for(decision))

    def test_two_prs_same_sha_see_one_native_status_but_cannot_share_receipt(self):
        publisher = SandboxPublisher(APP, enabled=True)
        first, second = fixture(), fixture()
        initial = run(publisher, first)
        self.assertTrue(initial.eligible)
        second["pull"].update(id=701, node_id="PR_43", number=43)
        second["open_pulls"] = [copy.deepcopy(second["pull"])]
        second["graph"]["pull"]["id"] = "PR_43"
        lens = second["graph"]["comments"][1]
        for edit in lens["userContentEdits"]["nodes"]:
            edit["diff"] = edit["diff"].replace("/pr/42/", "/pr/43/")
        set_body(second, 1, second["comments"][1]["body"].replace("/pr/42/", "/pr/43/"))
        second["checks"][-1]["details_url"] = second["checks"][-1]["details_url"].replace("/pull/42", "/pull/43")
        self.assertTrue(evaluate(second, 43).eligible)
        self.assertEqual(state(publisher), "success")
        self.assertIsNone(publisher.confirmed_for(evaluate(second, 43)))
        self.assertEqual(run(publisher, second).reason, "sandbox_shared_head")
        first["open_pulls"].append(copy.deepcopy(second["pull"]))
        self.assertEqual(run(publisher, first).reason, "ambiguous_head")
        self.assertEqual(state(publisher), "failure")

    def test_reopened_or_retargeted_pr_and_force_reset_block_reuse(self):
        for event in (
            "ReopenedEvent", "BaseRefChangedEvent", "HeadRefForcePushedEvent",
            "BaseRefForcePushedEvent", "HeadRefRestoredEvent", "ConvertToDraftEvent",
        ):
            with self.subTest(event=event):
                publisher = SandboxPublisher(APP, enabled=True)
                data = fixture()
                self.assertTrue(run(publisher, data).eligible)
                data["graph"]["pull"]["lifecycle"] = connection([{"__typename": event}])
                self.assertEqual(run(publisher, data).reason, "pr_lifecycle_requires_revalidation")
                self.assertEqual(state(publisher), "failure")

    def test_out_of_scope_pr_invalidates_local_receipt_without_native_revocation(self):
        publisher = SandboxPublisher(APP, enabled=True)
        data = fixture()
        original = run(publisher, data)
        self.assertIsNotNone(publisher.confirmed_for(original))
        data["pull"]["draft"] = True
        self.assertEqual(run(publisher, data).reason, "pr_out_of_scope")
        self.assertEqual(state(publisher), "success")
        self.assertIsNone(publisher.confirmed_for(original))

    def test_unfiltered_total_is_not_a_lifecycle_event(self):
        data = fixture()
        data["graph"]["pull"]["lifecycle"]["totalCount"] = 8
        self.assertTrue(evaluate(data, 42).eligible)
        data["graph"]["pull"]["lifecycle"]["pageInfo"]["hasNextPage"] = True
        self.assertEqual(evaluate(data, 42).reason, "pr_lifecycle_unavailable")

    def test_missed_events_leave_native_green_until_a_fresh_read(self):
        for change in ("edited", "deleted", "lens_findings"):
            with self.subTest(change=change):
                publisher = SandboxPublisher(APP, enabled=True)
                data = fixture()
                self.assertTrue(run(publisher, data).eligible)
                if change == "edited":
                    data["graph"]["comments"][0]["body"] += "\nUnexpected editor"
                elif change == "deleted":
                    data["comments"].pop(0)
                else:
                    set_body(data, 1, lens_finding_body())
                self.assertEqual(state(publisher), "success")
                self.assertIsNone(publisher.confirmed_for(evaluate(data, 42)))
                self.assertFalse(run(publisher, data).eligible)
                self.assertEqual(state(publisher), "failure")

    def test_duplicate_notifications_coalesce_into_one_evaluation(self):
        publisher = SandboxPublisher(APP, enabled=True)
        data = fixture()
        event = ("pull_request", {"action": "synchronize", "number": 42})
        events = [event, event, ("status", {"number": 42})]
        results = [run(publisher, data) for _ in event_candidates(events)]
        self.assertEqual(len(results), 1)
        self.assertEqual(publisher.visible(HEAD).generation, 1)

    def test_lost_ack_requires_fresh_manual_recovery(self):
        publisher = SandboxPublisher(APP, enabled=True)
        data = fixture()
        result = run(publisher, data, fault=("success", "after"))
        self.assertFalse(result.eligible)
        self.assertEqual(state(publisher), "success")
        self.assertIsNone(publisher.confirmed_for(evaluate(data, 42)))
        findings(data)
        self.assertFalse(run(publisher, data).eligible)
        self.assertEqual(state(publisher), "failure")

    def test_failed_revocation_can_leave_native_green_and_blocks_local_receipt(self):
        publisher = SandboxPublisher(APP, enabled=True, max_writes=2)
        data = fixture()
        decision = run(publisher, data)
        self.assertTrue(decision.eligible)
        self.assertEqual(run(publisher, data).reason, "sandbox_status_budget_exhausted")
        self.assertEqual(state(publisher), "success")
        self.assertIsNone(publisher.confirmed_for(decision))

    def test_scope_change_during_publication_never_sends_success(self):
        for field in ("head", "target_branch", "base_tip"):
            with self.subTest(field=field):
                publisher = SandboxPublisher(APP, enabled=True)
                data = fixture()
                moved = copy.deepcopy(data["pull"])
                if field == "head":
                    moved["head"]["sha"] = NEXT
                elif field == "target_branch":
                    moved["base"]["ref"] = "other"
                else:
                    moved["base_tip"] = NEXT
                pulls = iter([data["pull"], moved])
                result = publisher.run(42, lambda: data, lambda: next(pulls), actor_app_id=APP)
                self.assertFalse(result.eligible)
                self.assertEqual(state(publisher), "pending")

    def test_newer_failure_fences_older_success(self):
        publisher = SandboxPublisher(APP, enabled=True)
        older, newer = fixture(), fixture()
        findings(newer)
        started = False

        def old_read():
            nonlocal started
            if not started:
                started = True
                self.assertFalse(run(publisher, newer).eligible)
            return older

        result = publisher.run(42, old_read, lambda: older["pull"], actor_app_id=APP)
        self.assertEqual(result.reason, "sandbox_publication_superseded")
        self.assertEqual(state(publisher), "failure")

    def test_newer_failure_fences_older_invocation_before_pending(self):
        publisher = SandboxPublisher(APP, enabled=True)
        older, newer = fixture(), fixture()
        findings(newer)

        def old_initial_scope():
            self.assertEqual(run(publisher, newer).reason, "codex_findings")
            return older["pull"]

        result = publisher.run(42, lambda: older, old_initial_scope, actor_app_id=APP)
        self.assertEqual(result.reason, "sandbox_publication_superseded")
        self.assertEqual(state(publisher), "failure")
        self.assertIsNone(publisher.confirmed_for(evaluate(older, 42)))

    def test_late_lens_finding_blocks_second_read_before_simulated_success(self):
        publisher = SandboxPublisher(APP, enabled=True)
        earlier, later = fixture(), fixture()
        earlier["comments"].pop()
        late_rest, late_graph = comment("IC_late", 812, 320153949, "coldtea-pr-lens[bot]",
                                       4690539, "<!-- pr-lens:finding e30= -->")
        later["comments"].append(late_rest)
        later["graph"]["comments"].append(late_graph)
        reads = iter([earlier, later])
        result = publisher.run(42, lambda: next(reads), lambda: earlier["pull"], actor_app_id=APP)
        self.assertEqual(result.reason, "pr_lens_findings")
        self.assertEqual(state(publisher), "failure")

    def test_missing_codex_comment_through_real_collector_publishes_failure(self):
        data = fixture()
        data["comments"].pop(0)
        data["graph"]["comments"].pop(0)
        prefix = "repos/yoliverasPozo/AI_CONTEXT/"
        endpoints = {
            "git/ref/heads/main": {"ref": "refs/heads/main",
                                  "object": {"type": "commit", "sha": data["pull"]["base_tip"]}},
            "pulls/42": data["pull"],
            "issues/42/comments": data["comments"],
            "pulls": data["open_pulls"],
            f"commits/{HEAD}/check-runs": {"total_count": len(data["checks"]),
                                          "check_runs": data["checks"]},
            "actions/workflows/347167039/runs": {"total_count": len(data["runs"]),
                                               "workflow_runs": data["runs"]},
            "contents/.github/workflows/tests.yml": data["workflow_blobs"][0],
        }

        def request(endpoint, body=None):
            if endpoint == "graphql":
                self.assertEqual(json.loads(body)["variables"]["ids"], ["IC_lens"])
                return {"data": {"repository": {"pull": data["graph"]["pull"]},
                                 "comments": data["graph"]["comments"]}}
            return endpoints[endpoint.removeprefix(prefix).split("?", 1)[0]]

        api = GitHub(request=request)
        publisher = SandboxPublisher(APP, enabled=True)
        result = publisher.run(42, lambda: api.snapshot(42), lambda: api.pull(42), actor_app_id=APP)
        self.assertEqual(result.reason, "codex_comment_missing_or_ambiguous")
        self.assertEqual(state(publisher), "failure")

    def test_review_can_change_after_last_evidence_read(self):
        publisher = SandboxPublisher(APP, enabled=True)
        original, later = fixture(), fixture()
        reads = 0

        def last_scope_read():
            nonlocal reads
            reads += 1
            if reads == 2:
                findings(later)
            return original["pull"]

        self.assertTrue(publisher.run(42, lambda: original, last_scope_read, actor_app_id=APP).eligible)
        self.assertEqual(state(publisher), "success")
        self.assertIsNone(publisher.confirmed_for(evaluate(later, 42)))
