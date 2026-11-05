import copy
import unittest

from examples.review_gate.evaluator import evaluate, event_candidates
from examples.review_gate.publisher import SandboxPublisher
from tests.test_ai_review_gate import HEAD, NEXT, codex_body, connection, fixture, lens_body, set_body


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
                    data["comments"].pop()
                else:
                    body = lens_body(review="<details>\n<summary><b>1 finding</b></summary>")
                    set_body(data, 1, body)
                    data["graph"]["comments"][1]["userContentEdits"]["nodes"][0]["diff"] = body
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
