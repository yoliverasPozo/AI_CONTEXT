"""Single-item writer safety contracts, using an in-memory remote boundary."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from examples.project_sync.writer import prepare, apply, recover, rollback_proposal, WriterError
from examples.project_sync.writer_journal import Journal, JournalError

NOW = 2000000000
HEAD = "a" * 40


def state():
    return {"complete": True,
        "project": {"id": "PROJECT", "owner": "example", "owner_type": "user", "number": 1,
                    "public": False, "closed": False,
                    "fields": [{"id": "F_GATE", "name": "Approval gate", "dataType": "SINGLE_SELECT"}]},
        "items": [{"id": "OLD", "content_id": "PR_OLD", "kind": "PullRequest", "archived": False,
                   "values": [{"field_id": "F_GATE", "kind": "SingleSelect", "value": "Hold"}]}],
        "target": {"id": "PR_NEW", "repository": "example/widget", "number": 8,
                   "head_sha": HEAD, "state": "OPEN"}}


class Remote:
    def __init__(self, source=None):
        self.state = copy.deepcopy(source or state())
        self.adds = 0
        self.reads = 0
        self.failure = None
        self.modify_original = False

    def read(self):
        self.reads += 1
        if self.failure == "post-read" and self.adds:
            raise OSError("secret-containing service error")
        return copy.deepcopy(self.state)

    def add(self, project_id, content_id, operation_id):
        self.adds += 1
        assert project_id == "PROJECT" and content_id == "PR_NEW"
        self.state["items"].append({"id": "NEW", "content_id": content_id, "kind": "PullRequest",
                                   "archived": False, "values": []})
        if self.modify_original:
            self.state["items"][0]["values"][0]["value"] = "Human changed gate"
        if self.failure == "timeout":
            raise TimeoutError("secret transport output")
        return "NEW"


class WriterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.remote = Remote()
        self.proposal = prepare(self.remote.read(), "pilot-1", NOW, NOW+900)
        self.approval = {"action": "add_one", "operation_id": "pilot-1",
                         "proposal_sha256": self.proposal["sha256"], "project_id": "PROJECT",
                         "content_id": "PR_NEW", "expires_at": NOW+900}
        self.journal = Journal.create(Path(self.temp.name)/"operation", self.proposal)

    def execute(self, **kwargs):
        args = dict(enabled=True, execute=True, approval=self.approval, now=NOW+1, clock=lambda:NOW+1)
        args.update(kwargs)
        return apply(self.proposal, self.remote, self.journal, **args)

    def test_default_and_missing_execution_gate_never_contact_remote(self):
        for changes in ({"enabled": False}, {"execute": False}, {"approval": None}):
            with self.subTest(changes=changes), self.assertRaises(WriterError):
                self.execute(**changes)
        self.assertEqual(self.remote.adds, 0)
        self.assertEqual(self.remote.reads, 1)

    def test_success_adds_one_and_preserves_original_fields_in_durable_receipt(self):
        result = self.execute()
        self.assertEqual(result["status"], "verified_present")
        self.assertEqual(self.remote.adds, 1)
        self.assertEqual(self.remote.state["items"][0], state()["items"][0])
        reopened = Journal.open(self.journal.path)
        after = reopened.events()[-1]["data"]["after"]
        self.assertEqual(after["project"], self.remote.state["project"])
        self.assertEqual({i["id"]:i for i in after["items"]},
                         {i["id"]:i for i in self.remote.state["items"]})
        self.assertEqual(reopened.events()[-1]["data"]["ownership"], "not_proven")
        self.execute()
        self.assertEqual(self.remote.adds, 1)

    def test_wrong_approval_digest_or_expiry_refuses_before_remote(self):
        for key, value in (("proposal_sha256", "0"*64), ("project_id", "OTHER"),
                           ("content_id", "OTHER"), ("operation_id", "other"), ("expires_at", NOW)):
            approval = dict(self.approval, **{key:value})
            with self.subTest(key=key), self.assertRaises(WriterError):
                self.execute(approval=approval)
        self.assertEqual(self.remote.reads, 1)
        self.assertEqual(self.remote.adds, 0)

    def test_expected_head_or_project_field_drift_aborts_before_mutation(self):
        for change in ("head", "gate", "project"):
            self.remote.state = state()
            if change == "head": self.remote.state["target"]["head_sha"] = "b"*40
            if change == "gate": self.remote.state["items"][0]["values"][0]["value"] = "Changed"
            if change == "project": self.remote.state["project"]["public"] = True
            with self.subTest(change=change), self.assertRaises(WriterError): self.execute()
        self.assertEqual(self.remote.adds, 0)

    def test_preexisting_or_archived_target_is_never_added_or_unarchived(self):
        for archived in (False, True):
            remote = Remote()
            remote.state["items"].append({"id":"EXISTING", "content_id":"PR_NEW", "kind":"PullRequest", "archived":archived,"values":[]})
            journal = Journal.create(Path(self.temp.name)/str(archived), self.proposal)
            result = apply(self.proposal, remote, journal, enabled=True, execute=True, approval=self.approval, now=NOW+1)
            self.assertEqual(result["status"], "already_present")
            self.assertEqual(remote.adds, 0)
            self.assertEqual(remote.state["items"][-1]["archived"], archived)
            with self.assertRaises(WriterError): rollback_proposal(journal, remote.read())

    def test_timeout_recovers_read_only_without_resending_or_claiming_ownership(self):
        self.remote.failure = "timeout"
        self.assertEqual(self.execute()["status"], "uncertain")
        self.assertEqual(self.execute()["status"], "recovery_required")
        result = recover(self.journal, self.remote)
        self.assertEqual(result["status"], "present_after_uncertain")
        self.assertEqual(result["ownership"], "unknown")
        self.assertEqual(self.remote.adds, 1)
        with self.assertRaises(WriterError): rollback_proposal(self.journal, self.remote.read())

    def test_no_op_is_terminal_even_if_other_actor_later_removes_item(self):
        self.remote.state["items"].append({"id":"EXISTING", "content_id":"PR_NEW", "kind":"PullRequest", "archived":True,"values":[]})
        self.assertEqual(self.execute()["status"], "already_present")
        self.remote.state["items"].pop()
        self.assertEqual(self.execute()["status"], "already_present")
        self.assertEqual(self.remote.adds, 0)

    def test_crash_after_intent_even_before_send_is_spent(self):
        self.journal.append("intent", {"proposal_sha256":self.proposal["sha256"]})
        self.assertEqual(self.execute()["status"], "recovery_required")
        self.assertEqual(recover(self.journal, self.remote)["status"], "absent_after_uncertain")
        self.assertEqual(self.remote.adds, 0)

    def test_post_read_failure_or_changed_original_is_needs_review(self):
        self.remote.failure = "post-read"
        self.assertEqual(self.execute()["status"], "needs_review")
        self.assertEqual(self.remote.adds, 1)

    def test_drift_after_add_is_not_undone_or_reported_as_success(self):
        self.remote.modify_original = True
        self.assertEqual(self.execute()["status"], "needs_review")
        self.assertEqual(self.remote.state["items"][0]["values"][0]["value"], "Human changed gate")

    def test_rollback_only_proposes_exact_unmodified_item_for_manual_review(self):
        self.execute()
        proposal = rollback_proposal(self.journal, self.remote.read())
        self.assertEqual(proposal["item_id"], "NEW")
        self.assertFalse(proposal["executable"])
        self.assertFalse(proposal["ownership_proven"])
        self.assertEqual(self.remote.adds, 1)
        self.assertEqual(len(self.remote.state["items"]), 2)
        for change in ("field", "archived", "replaced", "original"):
            current = self.remote.read()
            if change == "field": current["items"][-1]["values"] = [{"field_id":"F_GATE","kind":"SingleSelect","value":"Human decision"}]
            if change == "archived": current["items"][-1]["archived"] = True
            if change == "replaced": current["items"][-1]["id"] = "OTHER"
            if change == "original": current["items"][0]["values"][0]["value"] = "Human decision"
            with self.subTest(change=change), self.assertRaises(WriterError): rollback_proposal(self.journal, current)

    def test_duplicate_or_incomplete_snapshot_refuses_preparation(self):
        for value in (dict(state(), complete=False), dict(state(), items=state()["items"]*2)):
            with self.assertRaises(WriterError): prepare(value, "new", NOW, NOW+60)

    def test_journal_corruption_or_lock_prevents_mutation(self):
        with self.journal.lock():
            with self.assertRaises(JournalError): self.execute()
        with (self.journal.path/"journal.jsonl").open("ab") as stream: stream.write(b'{"truncated":')
        with self.assertRaises(JournalError): self.execute()
        self.assertEqual(self.remote.adds, 0)

    def test_failed_intent_persistence_prevents_network_mutation(self):
        original = self.journal.append
        def broken(kind, data):
            if kind == "intent": raise OSError("disk full")
            return original(kind,data)
        self.journal.append = broken
        with self.assertRaises(OSError): self.execute()
        self.assertEqual(self.remote.adds, 0)

    def test_approval_expiring_during_preflight_prevents_send(self):
        with self.assertRaises(WriterError): self.execute(clock=lambda:NOW+901)
        self.assertEqual(self.remote.adds,0)

    def test_acknowledgment_receipt_failure_never_retries(self):
        original=self.journal.append
        def broken(kind,data):
            if kind=="acknowledged": raise OSError("disk full")
            return original(kind,data)
        self.journal.append=broken
        with self.assertRaises(OSError): self.execute()
        self.assertEqual(self.execute()["status"],"recovery_required")
        self.assertEqual(self.remote.adds,1)

    def test_server_side_concurrent_add_cannot_prove_ownership(self):
        def other_actor_add(*args):
            self.remote.state["items"].append({"id":"OTHER_ACTOR", "content_id":"PR_NEW", "kind":"PullRequest", "archived":False,"values":[]})
            return "OTHER_ACTOR"
        self.remote.add=other_actor_add
        result=self.execute()
        self.assertEqual(result["ownership"],"not_proven")
        self.assertFalse(rollback_proposal(self.journal,self.remote.read())["ownership_proven"])

    def test_recovery_receipt_bound_refuses_without_corrupting_existing_chain(self):
        self.execute()
        path=self.journal.path/"journal.jsonl"
        before=path.read_bytes()
        with patch("examples.project_sync.writer_journal.MAX_BYTES",len(before)+1):
            with self.assertRaises(JournalError): recover(self.journal,self.remote)
        self.assertEqual(before,path.read_bytes())
        self.assertEqual(Journal.open(self.journal.path).events()[-1]["kind"],"complete")

    def test_expiry_during_intent_fsync_spends_intent_without_send(self):
        times=iter((NOW+1,NOW+901))
        with self.assertRaises(WriterError): self.execute(clock=lambda:next(times))
        self.assertEqual(self.journal.events()[-1]["kind"],"intent")
        self.assertEqual(self.execute()["status"],"recovery_required")
        self.assertEqual(self.remote.adds,0)

    def test_final_receipt_persistence_failure_is_recoverable_without_resend(self):
        original=self.journal.append
        def broken(kind,data):
            if kind=="complete": raise OSError("disk full")
            return original(kind,data)
        self.journal.append=broken
        with self.assertRaises(OSError): self.execute()
        reopened=Journal.open(self.journal.path)
        self.assertEqual(recover(reopened,self.remote)["status"],"present_after_uncertain")
        self.assertEqual(self.execute()["status"],"recovery_required")
        self.assertEqual(self.remote.adds,1)
