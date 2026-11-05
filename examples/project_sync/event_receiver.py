"""Opt-in loopback pilot for signed GitHub PR hints and read-only observations."""

import argparse
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import re
import sqlite3
import time

from .collector import GhClient, gh_transport, whole_connection
from .planner import PlanError


MAX_BODY = 256 * 1024
MAX_READ_ATTEMPTS = 20
ACTIONS = {"opened", "synchronize", "reopened", "closed"}
SHA = re.compile(r"[a-f0-9]{40}")
NODE_ID = re.compile(r"[a-zA-Z0-9_=-]{1,128}")
REPOSITORY = re.compile(r"[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+")
DELIVERY = re.compile(r"[a-f0-9]{8}(-[a-f0-9]{4}){3}-[a-f0-9]{12}")
SIGNATURE = re.compile(r"sha256=[a-f0-9]{64}")
CONTENT_LENGTH = re.compile(r"[0-9]{1,6}")
QUERY = """query ProjectEventObservation($owner:String!, $name:String!, $number:Int!, $project:ID!) {
 repository(owner:$owner, name:$name) {
  databaseId nameWithOwner
  pullRequest(number:$number) {
   fullDatabaseId id number headRefOid state
   projectItems(first:100, includeArchived:true) {
    totalCount pageInfo { hasNextPage }
    nodes { id isArchived project { id } content { ... on PullRequest { id } } }
   }
  }
 }
 project: node(id:$project) { ... on ProjectV2 {
  id closed public owner { __typename ... on User { login } }
 } }
 rateLimit { remaining cost }
}"""


@dataclass(frozen=True)
class Scope:
    repository: str
    repository_id: int
    project_id: str

    def __post_init__(self):
        if (not REPOSITORY.fullmatch(self.repository) or type(self.repository_id) is not int
                or self.repository_id < 1 or not NODE_ID.fullmatch(self.project_id)):
            raise ValueError("invalid receiver scope")


class Rejected(ValueError):
    def __init__(self, status, code):
        super().__init__(code)
        self.status = status


def valid(pattern, value):
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def require(condition, status, code):
    if not condition:
        raise Rejected(status, code)


def signed_hint(scope, secret, event, delivery, signature, body):
    require(0 < len(body) <= MAX_BODY, 413, "invalid_body_size")
    expected = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
    require(valid(SIGNATURE, signature)
            and hmac.compare_digest(signature, expected), 403, "invalid_signature")
    require(valid(DELIVERY, delivery), 400, "invalid_delivery")
    try:
        payload = json.loads(body)
        repo = payload["repository"]
        require(repo["id"] == scope.repository_id and repo["full_name"] == scope.repository,
                403, "repository_out_of_scope")
        if event == "ping" and "pull_request" not in payload and isinstance(payload.get("zen"), str):
            return None
        require(event == "pull_request", 400, "invalid_event_type")
        action = payload["action"]
        require(isinstance(action, str), 400, "invalid_event")
        if action not in ACTIONS:
            return None
        number, pull = payload["number"], payload["pull_request"]
        require(type(number) is int and 0 < number < 2**31 and pull["number"] == number
                and type(pull["id"]) is int and pull["id"] > 0 and valid(NODE_ID, pull["node_id"])
                and pull["base"]["repo"]["id"] == scope.repository_id
                and valid(SHA, pull["head"]["sha"]) and type(pull["merged"]) is bool,
                400, "invalid_pull_request_hint")
    except Rejected:
        raise
    except (TypeError, KeyError, ValueError, RecursionError):
        raise Rejected(400, "invalid_event") from None
    return (number, pull["id"], pull["node_id"], pull["head"]["sha"], action, pull["merged"])


def read_current(scope, hint, transport):
    number, database_id, node, event_head, action, event_merged = hint
    owner, name = scope.repository.split("/")
    api = GhClient({"max_calls": 1, "rate_floor": 200}, transport)
    try:
        data = api.query(QUERY, {"owner": owner, "name": name, "number": number, "project": scope.project_id})
        repo, project = data["repository"], data["project"]
        require(repo["databaseId"] == scope.repository_id and repo["nameWithOwner"] == scope.repository
                and project["id"] == scope.project_id and project["public"] is False and project["closed"] is False
                and project["owner"] == {"__typename": "User", "login": owner}, 503, "scope_unverified")
        pull = repo["pullRequest"]
        require(pull["id"] == node and pull["fullDatabaseId"] == str(database_id)
                and pull["number"] == number and valid(SHA, pull["headRefOid"])
                and pull["state"] in {"OPEN", "CLOSED", "MERGED"}, 503, "pull_unverified")
        items = whole_connection(pull["projectItems"])
        matches = [item for item in items if item["project"]["id"] == scope.project_id]
        require(len(matches) <= 1, 503, "membership_unverified")
        membership, item_id = "absent", None
        if matches:
            item = matches[0]
            require(valid(NODE_ID, item["id"]) and item["content"]["id"] == node
                    and type(item["isArchived"]) is bool, 503, "membership_unverified")
            item_id = item["id"]
            membership = "archived" if item["isArchived"] else "active"
    except (KeyError, TypeError, PlanError):
        raise Rejected(503, "targeted_read_failed") from None
    state, head = pull["state"], pull["headRefOid"]
    expected = ("MERGED" if event_merged else "CLOSED") if action == "closed" else "OPEN"
    return {"state": state, "head": head, "membership": membership, "item": item_id,
            "stale_hint": state != expected or head != event_head, "rate_remaining": api.remaining}


class Receiver:
    def __init__(self, scope, ledger, secret, transport=None):
        if len(secret) < 32:
            raise ValueError("webhook secret must be at least 32 bytes")
        self.scope = scope
        self.ledger = Path(ledger)
        self.secret = secret
        self.transport = transport or (lambda query, variables: gh_transport(query, variables, timeout=4))

    def accept(self, event, delivery, signature, body):
        hint = signed_hint(self.scope, self.secret, event, delivery, signature, body)
        if hint is None:
            return None
        digest = hashlib.sha256(body).hexdigest()
        number, database_id, node, event_head, action, _ = hint
        failure = None
        try:
            with closing(sqlite3.connect(self.ledger, timeout=0)) as db, db:
                db.execute("PRAGMA synchronous = FULL")
                db.execute("BEGIN IMMEDIATE")
                db.execute("""CREATE TABLE IF NOT EXISTS budget (
                    slot INTEGER PRIMARY KEY CHECK(slot = 1), scope TEXT NOT NULL, attempts INTEGER NOT NULL,
                    last_failure TEXT)""")
                db.execute("""CREATE TABLE IF NOT EXISTS deliveries (
                    id TEXT PRIMARY KEY, digest TEXT UNIQUE NOT NULL, pr_node TEXT NOT NULL,
                    receipt TEXT NOT NULL)""")
                scope = f"{self.scope.repository}/{self.scope.repository_id}/{self.scope.project_id}"
                db.execute("INSERT OR IGNORE INTO budget VALUES (1, ?, 0, NULL)", (scope,))
                recorded_scope, attempts = db.execute("SELECT scope, attempts FROM budget WHERE slot = 1").fetchone()
                require(recorded_scope == scope, 503, "ledger_scope_mismatch")
                previous = db.execute("SELECT digest FROM deliveries WHERE id = ?", (delivery,)).fetchone()
                require(previous is None or previous == (digest,), 409, "delivery_conflict")
                if previous:
                    return {"outcome": "duplicate"}
                require(db.execute("SELECT 1 FROM deliveries WHERE digest = ?", (digest,)).fetchone() is None,
                        409, "delivery_conflict")
                require(attempts < MAX_READ_ATTEMPTS, 503, "read_budget_exhausted")
                db.execute("UPDATE budget SET attempts = attempts + 1 WHERE slot = 1")
                try:
                    current = read_current(self.scope, hint, self.transport)
                except Rejected as error:
                    failure = error
                    db.execute("UPDATE budget SET last_failure = ? WHERE slot = 1", (str(error),))
                else:
                    latest = db.execute(
                        "SELECT receipt FROM deliveries WHERE pr_node = ? ORDER BY rowid DESC LIMIT 1",
                        (node,)).fetchone()
                    old = json.loads(latest[0]) if latest else {}
                    unchanged = all(old.get(key) == current[key] for key in ("state", "head", "membership", "item"))
                    receipt = {"outcome": "unchanged" if unchanged else "observed",
                               "received_at": datetime.now(timezone.utc).isoformat(), "delivery": delivery,
                               "repository": self.scope.repository, "repository_id": self.scope.repository_id,
                               "project": self.scope.project_id, "pr_number": number, "pr_database_id": database_id,
                               "pr_node": node, "action": action, "event_head": event_head, **current}
                    db.execute("INSERT INTO deliveries VALUES (?, ?, ?, ?)",
                               (delivery, digest, node, json.dumps(receipt, sort_keys=True)))
                    return receipt
        except (sqlite3.Error, OSError, json.JSONDecodeError):
            raise Rejected(503, "ledger_unavailable") from None
        raise failure


def build_server(port, receiver):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            self.request.settimeout(2)
            super().setup()

        def log_message(self, *args):
            pass

        def send_error(self, code, *args, **kwargs):
            self.respond(code)

        def respond(self, status):
            self.send_response_only(status)
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()

        def one_header(self, name):
            values = self.headers.get_all(name, [])
            require(len(values) == 1, 400, "invalid_headers")
            return values[0]

        def do_POST(self):
            try:
                require(self.path == "/github/pr", 404, "unknown_path")
                require("Transfer-Encoding" not in self.headers, 400, "invalid_headers")
                length = self.one_header("Content-Length")
                require(valid(CONTENT_LENGTH, length) and 0 < int(length) <= MAX_BODY,
                        413, "invalid_body_size")
                body = self.rfile.read(int(length))
                require(len(body) == int(length), 400, "invalid_body_size")
                result = receiver.accept(self.one_header("X-GitHub-Event"), self.one_header("X-GitHub-Delivery"),
                                         self.one_header("X-Hub-Signature-256"), body)
                self.respond(204 if result is None else 200)
            except Rejected as error:
                self.respond(error.status)
            except OSError:
                self.close_connection = True

    class Server(HTTPServer):
        def handle_error(self, request, client_address):
            # HTTPServer's default handler prints unsanitized tracebacks.
            pass

    return Server(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--repository-id", required=True, type=int)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--seconds", type=int, default=1800)
    args = parser.parse_args()
    if (not 1 <= args.seconds <= 3600 or not 1024 <= args.port <= 65535
            or not args.ledger.is_absolute() or not args.ledger.parent.is_dir()):
        parser.error("use a bounded window, a nonprivileged port, and a private existing ledger directory")
    try:
        scope = Scope(args.repository, args.repository_id, args.project_id)
        receiver = Receiver(scope, args.ledger, os.environ.get("AI_CONTEXT_WEBHOOK_SECRET", "").encode())
        with build_server(args.port, receiver) as server:
            deadline = time.monotonic() + args.seconds
            while time.monotonic() < deadline:
                server.timeout = min(0.5, max(0, deadline - time.monotonic()))
                server.handle_request()
    except (ValueError, OSError):
        parser.exit(2, "receiver unavailable\n")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
