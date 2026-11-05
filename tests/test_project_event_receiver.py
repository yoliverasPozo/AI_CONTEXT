from contextlib import closing
import hashlib
import hmac
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from uuid import UUID

from examples.project_sync.event_receiver import Receiver, Rejected, Scope, build_server


SCOPE = Scope("example/widget", 123, "PROJECT_1")
SECRET = b"synthetic-only-0123456789abcdef0123456789abcdef"
HEAD = "a" * 40
NEXT = "b" * 40


def delivery(number):
    return str(UUID(int=number))


def message(*, action="opened", head=HEAD, merged=False, number=42, marker=""):
    return json.dumps({
        "action": action, "number": number,
        "repository": {"id": 123, "full_name": "example/widget"},
        "pull_request": {"id": 456, "node_id": "PR_42", "number": number,
                         "head": {"sha": head}, "base": {"repo": {"id": 123}},
                         "merged": merged, "body": marker},
    }).encode()


def sign(body):
    return "sha256=" + hmac.new(SECRET, body, hashlib.sha256).hexdigest()


def response(*, head=HEAD, state="OPEN", archived=False, remaining=500):
    items = [] if archived is None else [
        {"id": "ITEM_42", "isArchived": archived, "project": {"id": "PROJECT_1"},
         "content": {"id": "PR_42"}}
    ]
    return {"data": {"repository": {"databaseId": 123, "nameWithOwner": "example/widget",
        "pullRequest": {"id": "PR_42", "fullDatabaseId": "456", "number": 42,
                        "headRefOid": head, "state": state, "baseRefName": "main",
                        "projectItems": {"nodes": items, "totalCount": len(items),
                                         "pageInfo": {"hasNextPage": False}}}},
        "project": {"id": "PROJECT_1", "public": False, "closed": False,
                    "owner": {"__typename": "User", "login": "example"}},
        "rateLimit": {"cost": 1, "remaining": remaining}}}


class EventReceiverTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.ledger = Path(self.directory.name) / "events.sqlite3"
        self.reads = []
        self.api_response = response()

    def transport(self, query, variables):
        self.assertTrue(query.startswith("query "))
        self.assertIn("includeArchived:true", query)
        self.assertEqual(variables, {"owner": "example", "name": "widget",
                                     "number": 42, "project": "PROJECT_1"})
        self.reads.append(variables)
        return self.api_response

    def receiver(self):
        return Receiver(SCOPE, self.ledger, SECRET, self.transport)

    def accept(self, receiver, n, body=None):
        body = message() if body is None else body
        return receiver.accept("pull_request", delivery(n), sign(body), body)

    def test_duplicate_survives_restart_and_receipt_omits_raw_text(self):
        body = message(marker="untrusted text to exclude")
        first = self.accept(self.receiver(), 1, body)
        self.assertEqual(first["outcome"], "observed")
        self.assertEqual(first["pr_node"], "PR_42")
        self.assertEqual(self.accept(self.receiver(), 1, body)["outcome"], "duplicate")
        with self.assertRaises(Rejected) as alias:
            self.accept(self.receiver(), 2, body)
        self.assertEqual(alias.exception.status, 409)
        self.assertEqual(len(self.reads), 1)
        self.assertNotIn(b"untrusted text", self.ledger.read_bytes())
        with self.assertRaises(Rejected) as error:
            self.accept(self.receiver(), 1, message(action="synchronize"))
        self.assertEqual(error.exception.status, 409)

    def test_duplicate_survives_a_separate_process(self):
        self.accept(self.receiver(), 1)
        command = """
from pathlib import Path
import sys
from tests.test_project_event_receiver import SCOPE, SECRET, delivery, message, sign
from examples.project_sync.event_receiver import Receiver
def no_read(*args):
    raise AssertionError("duplicate read GitHub")
body = message()
receiver = Receiver(SCOPE, Path(sys.argv[1]), SECRET, no_read)
assert receiver.accept("pull_request", delivery(1), sign(body), body) == {"outcome": "duplicate"}
"""
        result = subprocess.run([sys.executable, "-c", command, str(self.ledger)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_stale_event_reports_current_head_lifecycle_and_archive(self):
        self.api_response = response(head=NEXT, state="MERGED", archived=True)
        receiver = self.receiver()
        merged = self.accept(receiver, 1, message(action="closed", head=NEXT, merged=True))
        late_open = self.accept(receiver, 2, message())
        self.assertEqual(merged["state"], "MERGED")
        self.assertEqual(late_open["head"], NEXT)
        self.assertEqual(late_open["membership"], "archived")
        self.assertTrue(late_open["stale_hint"])
        self.assertEqual(late_open["outcome"], "unchanged")

    def test_denied_or_incomplete_read_leaves_event_available_for_replay(self):
        self.api_response = response(remaining=199)
        with self.assertRaises(Rejected) as error:
            self.accept(self.receiver(), 1)
        self.assertEqual(error.exception.status, 503)
        self.api_response = response(archived=None)
        self.assertEqual(self.accept(self.receiver(), 1)["membership"], "absent")
        self.assertEqual(len(self.reads), 2)

    def test_failed_attempt_budget_survives_restart(self):
        self.api_response = response(remaining=199)
        with patch("examples.project_sync.event_receiver.MAX_READ_ATTEMPTS", 2):
            for _ in range(2):
                with self.assertRaises(Rejected):
                    self.accept(self.receiver(), 1)
            self.api_response = response()
            with self.assertRaises(Rejected) as exhausted:
                self.accept(self.receiver(), 1)
            self.assertEqual(str(exhausted.exception), "read_budget_exhausted")
        self.assertEqual(len(self.reads), 2)

    def test_target_identity_and_membership_must_be_complete(self):
        for changed in ("database_id", "truncated", "duplicate", "wrong_item"):
            with self.subTest(changed=changed):
                data = response()["data"]
                pr = data["repository"]["pullRequest"]
                items = pr["projectItems"]
                if changed == "database_id":
                    pr["fullDatabaseId"] = "999"
                elif changed == "truncated":
                    items["pageInfo"]["hasNextPage"] = True
                elif changed == "duplicate":
                    items["nodes"].append(items["nodes"][0])
                    items["totalCount"] = 2
                else:
                    items["nodes"][0]["content"]["id"] = "PR_OTHER"
                self.api_response = {"data": data}
                with self.assertRaises(Rejected):
                    self.accept(self.receiver(), 1)

    def test_bad_signature_and_wrong_scope_do_not_read_or_write(self):
        receiver = self.receiver()
        bad = json.loads(message())
        bad["repository"]["id"] = 222
        invalid_scope = json.dumps(bad).encode()
        for body, signature in [(message(), "sha256=" + "0" * 64),
                                (invalid_scope, sign(invalid_scope))]:
            with self.assertRaises(Rejected):
                receiver.accept("pull_request", delivery(1), signature, body)
        self.assertEqual(self.reads, [])
        self.assertFalse(self.ledger.exists())

    def test_loopback_http_ack_follows_durable_commit(self):
        with build_server(0, self.receiver()) as server:
            work = threading.Thread(target=server.handle_request, daemon=True)
            work.start()
            body = message()
            url = f"http://127.0.0.1:{server.server_port}/github/pr"
            request = Request(url, body, headers={"X-GitHub-Event": "pull_request",
                              "X-GitHub-Delivery": delivery(1), "X-Hub-Signature-256": sign(body)})
            with urlopen(request, timeout=3) as reply:
                self.assertEqual(reply.status, 200)
                self.assertEqual(reply.read(), b"")
            work.join(timeout=3)
            self.assertFalse(work.is_alive())
        with closing(sqlite3.connect(self.ledger)) as ledger:
            self.assertEqual(ledger.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0], 1)
