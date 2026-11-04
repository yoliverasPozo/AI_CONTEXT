"""Failures must remain stopped and explainable without persisting error text."""
import json
import subprocess
import unittest
import tempfile
from pathlib import Path

from tests import test_project_writer as fixture
from tests.test_project_writer_github import Wire, config
from examples.project_sync.writer import recover, prepare, apply
from examples.project_sync.writer_github import Backend, ADD_ONE
from examples.project_sync.writer_journal import Journal
from tests.test_project_writer_github import conn

state = fixture.state


class DiagnosticPolicyTests(unittest.TestCase):
    # Reuse the real temporary Journal/policy setup, not the inherited test suite.
    setUp = fixture.WriterTests.setUp
    execute = fixture.WriterTests.execute

    def test_post_transport_error_is_sanitized_and_never_retried(self):
        self.remote.failure="post-read"
        result=self.execute()
        self.assertEqual(result["status"],"needs_review")
        self.assertEqual(result["diagnostic"]["code"],"transport_error")
        self.assertEqual(result["diagnostic"]["phase"],"readback")
        self.assertNotIn("secret-containing",json.dumps(self.journal.events()))
        self.assertEqual(self.execute()["status"],"recovery_required")
        self.assertEqual(self.remote.adds,1)

    def test_changed_original_records_observation_without_compensation(self):
        self.remote.modify_original=True
        result=self.execute()
        self.assertEqual(result["diagnostic"]["code"],"original_item_changed")
        event=self.journal.events()[-1]
        self.assertEqual(event["data"]["observed"]["items"][1]["values"][0]["value"],"Human changed gate")
        self.assertEqual(result["diagnostic"]["phase"],"verify_addition")
        self.assertEqual(self.remote.adds,1)

    def test_not_yet_visible_add_is_diagnosed_and_later_recovery_only_reads(self):
        original=self.remote.read
        def read():
            return state() if self.remote.adds else original()
        self.remote.read=read
        result=self.execute()
        self.assertEqual(result["diagnostic"]["code"],"target_absent")
        self.assertEqual(self.journal.events()[-1]["data"]["observed"]["items"],state()["items"])
        self.remote.read=original
        self.assertEqual(recover(self.journal,self.remote)["status"],"present_after_uncertain")
        self.assertEqual(self.remote.adds,1)

    def test_generic_exception_message_and_class_name_never_escape(self):
        class PrivateEndpointAndTokenError(Exception): pass
        original=self.remote.read
        def read():
            if self.remote.adds:raise PrivateEndpointAndTokenError("bearer-private-value endpoint-private")
            return original()
        self.remote.read=read
        result=self.execute()
        self.assertEqual(result["diagnostic"]["code"],"unexpected_error")
        receipt=json.dumps(self.journal.events())
        for secret in ("PrivateEndpointAndTokenError","bearer-private-value","endpoint-private"):
            self.assertNotIn(secret,receipt)

    def test_changed_response_identity_or_archive_remains_needs_review(self):
        original=self.remote.add
        def add(*args):
            original(*args)
            return "DIFFERENT_ACK"
        self.remote.add=add
        self.assertEqual(self.execute()["diagnostic"]["code"],"target_item_mismatch")
        self.assertEqual(self.remote.adds,1)

    def test_archived_response_item_is_not_unarchived_or_deleted(self):
        original=self.remote.add
        def add(*args):
            result=original(*args);self.remote.state["items"][-1]["archived"]=True;return result
        self.remote.add=add
        self.assertEqual(self.execute()["diagnostic"]["code"],"target_archived")
        self.assertTrue(self.remote.state["items"][-1]["archived"])
        self.assertEqual(self.remote.adds,1)

    def test_failure_to_persist_diagnostic_cannot_regain_permission_to_send(self):
        self.remote.failure="post-read"
        original=self.journal.append
        def append(kind,data):
            if kind=="needs_review":raise OSError("disk full private path")
            original(kind,data)
        self.journal.append=append
        with self.assertRaises(OSError):self.execute()
        self.assertEqual(self.execute()["status"],"recovery_required")
        self.assertEqual(self.remote.adds,1)


class DiagnosticReaderTests(unittest.TestCase):
    def test_rate_floor_failure_retains_budget_evidence_without_raw_data(self):
        wire=Wire()
        def transport(document,variables):
            response=wire(document,variables)
            response["data"]["rateLimit"]["remaining"]=99
            return response
        backend=Backend(config(),transport=transport)
        with self.assertRaises(Exception):backend.read()
        evidence=backend.read_evidence
        self.assertEqual(evidence["failure_code"],"rate_floor_reached")
        self.assertEqual(evidence["rate_floor"],100)
        self.assertEqual(evidence["pages"][0]["remaining"],99)
        self.assertNotIn("Gate",json.dumps(evidence))

    def test_timeout_has_its_own_classification(self):
        def transport(*args):raise subprocess.TimeoutExpired("private command",45,output="private token")
        backend=Backend(config(),transport=transport)
        with self.assertRaises(Exception):backend.read()
        self.assertEqual(backend.read_evidence["failure_code"],"transport_timeout")
        self.assertNotIn("private",json.dumps(backend.read_evidence))

    def test_complete_read_records_counts_and_hashed_identities_only(self):
        backend=Backend(config(),transport=Wire())
        backend.read()
        evidence=backend.read_evidence
        self.assertEqual(evidence["pages"][0]["node_count"],1)
        self.assertEqual(evidence["pages"][0]["total_count"],1)
        self.assertEqual(evidence["pages"][0]["cost"],1)
        self.assertEqual(len(evidence["pages"][0]["items_sha256"]),64)
        self.assertNotIn("I_OLD",json.dumps(evidence))

    def test_access_and_json_failures_keep_specific_sanitized_outer_code(self):
        for error,expected in ((subprocess.CalledProcessError(1,"private-command",stderr="read:project private-token"),"read_access_denied"),
                               (json.JSONDecodeError("private-token","private-document",0),"transport_or_json_error")):
            def transport(*args):raise error
            backend=Backend(config(),transport=transport)
            with self.assertRaises(Exception):backend.read()
            self.assertEqual(backend.read_evidence["failure_code"],expected)
            self.assertNotIn("private",json.dumps(backend.read_evidence))

    def test_next_read_resets_old_failure_and_pages(self):
        wire=Wire();backend=Backend(config(),transport=wire)
        wire.item["content"]=None
        with self.assertRaises(Exception):backend.read()
        self.assertEqual(backend.read_evidence["failure_code"],"unreadable_node")
        wire.item["content"]={"__typename":"Issue","id":"I_OLD"}
        backend.read()
        self.assertNotIn("failure_code",backend.read_evidence)
        self.assertEqual(len(backend.read_evidence["pages"]),1)


class PaginatedHypothesisTests(unittest.TestCase):
    def test_distinct_transient_failures_can_match_same_six_call_cost_trace(self):
        # Two counterexamples disprove that the historical aggregate alone can
        # identify a root cause. Both exercise real Backend+policy+journal.
        for mode,want in (("absent","target_absent"),("null_relation","unreadable_field_relation")):
            wire=Wire();added=False;reconciling=False
            wire.project["fields"]["nodes"].append({"__typename":"ProjectV2Field","id":"F_REPO","name":"Repository","dataType":"REPOSITORY"})
            wire.project["fields"]["totalCount"]=2
            originals=[]
            import copy
            for index in range(45):
                item=copy.deepcopy(wire.item);item["id"]=f"ITEM_{index:03}";item["content"]["id"]=f"PR_{index:03}";originals.append(item)
            def transport(document,variables):
                nonlocal added
                if document==ADD_ONE:
                    added=True
                    return {"data":{"addProjectV2ItemById":{"item":{"id":"NEW"},"clientMutationId":variables["operation"]}}}
                response=wire(document,variables)
                rows=copy.deepcopy(originals)
                if added and (mode!="absent" or reconciling):
                    repository={"id":"REPO","nameWithOwner":"example/widget"} if reconciling else None
                    rows.append({"id":"NEW","isArchived":False,"content":{"__typename":"PullRequest","id":"PR_NEW"},
                                 "fieldValues":conn([{"__typename":"ProjectV2ItemFieldRepositoryValue","field":{"id":"F_REPO"},"repository":repository}])})
                start=int(variables["cursor"] or 0);batch=rows[start:start+20];end=start+len(batch)
                response["data"]["project"]["items"]={"nodes":batch,"totalCount":len(rows),"pageInfo":{"hasNextPage":end<len(rows),"endCursor":str(end)}}
                response["data"]["rateLimit"]={"cost":20,"remaining":4000}
                return response
            cfg=config();cfg["enabled"]=True
            before=Backend(cfg,transport=transport).read()
            proposal=prepare(before,"synthetic",fixture.NOW,fixture.NOW+900)
            approval={"action":"add_one","operation_id":"synthetic","proposal_sha256":proposal["sha256"],"project_id":"PROJECT","content_id":"PR_NEW","expires_at":fixture.NOW+900}
            with tempfile.TemporaryDirectory() as temp:
                journal=Journal.create(Path(temp)/"operation",proposal)
                backend=Backend(cfg,transport=transport,armed=True)
                result=apply(proposal,backend,journal,enabled=True,execute=True,approval=approval,now=fixture.NOW+1,clock=lambda:fixture.NOW+1)
                self.assertEqual(result["status"],"needs_review")
                self.assertEqual(result["diagnostic"]["code"],want)
                self.assertEqual(backend.metrics,{"read_calls":6,"read_points":120,"mutation_attempts":1})
                self.assertEqual(len(result["diagnostic"]["read_evidence"]["pages"]),3)
                reconciling=True
                self.assertEqual(recover(journal,backend)["status"],"present_after_uncertain")
                self.assertEqual(backend.metrics["mutation_attempts"],1)
