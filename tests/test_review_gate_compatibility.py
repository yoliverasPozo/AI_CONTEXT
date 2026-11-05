import copy
import json
import unittest

from examples.review_gate.evaluator import DISPOSITION_ACCEPT, DISPOSITION_MARKER, evaluate
from examples.review_gate.publisher import SandboxPublisher
from tests.test_ai_review_gate import BASE, HEAD, NEXT, TIME, connection, fixture, lens_finding_body, marker, set_body


SKIP = """<!-- pr-lens:sticky -->

> [!NOTE]
> Nothing here is code, only docs, data or images, so PR Lens left this pull request undrawn. Comment `@pr-lens draw` to draw it

<sub>`github.comment.notice: false` in `.github/pr-lens.yml` turns this note off</sub>"""

PR16_PATHS = (
    "AGENTS.md", "docs/AI_CONTEXT.md", "docs/COORDINATION.md",
    "docs/sessions/2026-11-05-pr-review-readiness.md", "examples/AGENTS.md",
    "examples/CHATGPT_WORK.md", "src/ai_context/resources/AGENTS.md",
    "src/ai_context/resources/CHATGPT_WORK.md", "src/ai_context/resources/COORDINATION.md",
    "src/ai_context/resources/HANDOFF.md", "templates/HANDOFF.md",
)


def skip_fixture(paths=("CHANGELOG.md",)):
    data = fixture()
    data["checks"].pop()
    lens = data["graph"]["comments"][1]
    lens.update(editor=None, lastEditedAt=None, includesCreatedEdit=False,
                userContentEdits=connection([]))
    set_body(data, 1, SKIP)
    before, after, files = [], [], []
    for name in paths:
        before.append({"path": name, "type": "blob", "mode": "100644", "sha": BASE})
        after.append(dict(before[-1], sha=NEXT))
        files.append({"filename": name, "status": "modified", "sha": NEXT})
    data["pull"]["changed_files"] = len(files)
    data["changes"] = {
        "comparison": {"base_commit": {"sha": BASE}, "merge_base_commit": {
            "sha": BASE, "commit": {"tree": {"sha": "d" * 40}},
        }},
        "head_commit": {"sha": HEAD, "tree": {"sha": "e" * 40}},
        "base_tree": {"sha": "d" * 40, "truncated": False, "tree": before},
        "head_tree": {"sha": "e" * 40, "truncated": False, "tree": after},
        "files": files,
    }
    return data


def attest(data, payload, owner=8781658):
    review = {"id": "PRR_owner", "author": {"__typename": "User", "databaseId": owner},
              "commit": {"oid": data["pull"]["head"]["sha"]}, "state": "COMMENTED",
              "submittedAt": "2026-11-05T13:00:00Z",
              "lastEditedAt": None, "editor": None, "isMinimized": False,
              "includesCreatedEdit": False, "userContentEdits": connection([]),
              "body": DISPOSITION_ACCEPT + "\n\n"
              + marker(DISPOSITION_MARKER, payload) + "\n\nReviewed the diff."}
    data["graph"]["pull"]["reviews"] = connection([review])
    return review


def finding_fixture(paths=("CHANGELOG.md",)):
    data = skip_fixture(paths)
    set_body(data, 1, lens_finding_body())
    return data


class AdvisoryTests(unittest.TestCase):
    def test_pr16_notice_is_advisory_without_a_waiver(self):
        head = "93fdc2427aaa32af51fca442034436f065b8b5c2"
        data = json.loads(json.dumps(skip_fixture(PR16_PATHS)).replace(HEAD, head))
        data["pull"].update(number=16, id=5173385648, node_id="PR_kwDOUHmmcs8AAAABNFuZsA")
        data["open_pulls"] = [copy.deepcopy(data["pull"])]
        data["graph"]["pull"]["id"] = data["pull"]["node_id"]
        del data["changes"]
        decision = evaluate(data, 16)
        self.assertTrue(decision.eligible)
        self.assertEqual(decision.evidence["pr_lens_outcome"], "intentional_skip")
        self.assertNotIn("disposition", decision.evidence)

    def test_known_findings_require_disposition_in_each_change_class(self):
        for paths, category in (
            (("CHANGELOG.md",), "ordinary_documentation"),
            (PR16_PATHS, "sensitive_documentation"),
            (("CHANGELOG.md", "src/example.py"), "executable_or_mixed"),
        ):
            with self.subTest(category=category):
                data = finding_fixture(paths)
                decision = evaluate(data, 42)
                self.assertEqual(decision.reason, "pr_lens_findings")
                self.assertEqual(decision.evidence["changes"]["class"], category)
                self.assertFalse(decision.eligible)
                attest(data, decision.evidence["disposition_request"])
                result = evaluate(data, 42)
                self.assertTrue(result.eligible)
                self.assertEqual(result.evidence["pr_lens_outcome"], "findings_dispositioned")

    def test_unknown_or_incomplete_diff_blocks_disposition(self):
        for case in ("truncated", "omitted", "wrong_head", "wrong_blob", "wrong_base"):
            with self.subTest(case=case):
                data = finding_fixture()
                if case == "truncated":
                    data["changes"]["head_tree"]["truncated"] = True
                elif case == "omitted":
                    data["changes"]["head_tree"]["tree"].append({
                        "path": "evil.py", "mode": "100644", "type": "blob", "sha": NEXT,
                    })
                elif case == "wrong_head":
                    data["changes"]["head_commit"]["sha"] = NEXT
                elif case == "wrong_base":
                    data["changes"]["comparison"]["base_commit"]["sha"] = NEXT
                else:
                    data["changes"]["files"][0]["sha"] = BASE
                self.assertEqual(evaluate(data, 42).reason, "change_evidence_invalid")

    def test_renaming_sensitive_instruction_into_ordinary_path_stays_sensitive(self):
        data = finding_fixture()
        data["changes"]["base_tree"]["tree"][0]["path"] = "AGENTS.md"
        data["changes"]["files"][0].update(status="renamed", previous_filename="AGENTS.md")
        result = evaluate(data, 42)
        self.assertEqual(result.evidence["changes"]["class"], "sensitive_documentation")

    def test_disposition_cannot_be_spoofed_edited_or_reused(self):
        for case in ("wrong_owner", "edited", "wrong_head", "wrong_diff", "wrong_findings"):
            with self.subTest(case=case):
                data = finding_fixture()
                request = copy.deepcopy(evaluate(data, 42).evidence["disposition_request"])
                if case == "wrong_diff":
                    request["files_sha256"] = "0" * 64
                if case == "wrong_findings":
                    request["findings"][0]["sha256"] = "0" * 64
                review = attest(data, request, 23 if case == "wrong_owner" else 8781658)
                if case == "edited":
                    review["lastEditedAt"] = TIME
                if case == "wrong_head":
                    review["commit"]["oid"] = NEXT
                self.assertFalse(evaluate(data, 42).eligible)

    def test_disposition_timestamps_are_parsed_and_compared_with_offsets(self):
        for submitted, eligible in (
            ("invalid-timestamp", False),
            ("2026-11-05T13:10:00", False),
            ("2026-11-05T14:30:00+00:60", False),
            ("2026-11-05T12:59:33Z", False),
            ("2026-11-05T13:10:00+01:00", False),
            ("2026-11-05T09:01:00-04:00", True),
        ):
            with self.subTest(submitted=submitted):
                data = finding_fixture()
                review = attest(data, evaluate(data, 42).evidence["disposition_request"])
                review["submittedAt"] = submitted
                self.assertEqual(evaluate(data, 42).eligible, eligible)

    def test_disposition_preserves_codex_ci_and_conversation_requirements(self):
        for case, reason in (
            ("codex", "codex_stale"), ("ci", "ci_checks_incomplete"),
            ("thread", "unresolved_review_thread"),
        ):
            with self.subTest(case=case):
                data = finding_fixture()
                attest(data, evaluate(data, 42).evidence["disposition_request"])
                if case == "codex":
                    original = data["comments"][0]["body"]
                    set_body(data, 0, original.replace(HEAD, NEXT))
                elif case == "ci":
                    data["checks"][0]["conclusion"] = "failure"
                else:
                    data["graph"]["pull"]["reviewThreads"] = connection([{"id": "RT", "isResolved": False}])
                self.assertEqual(evaluate(data, 42).reason, reason)

    def test_disposition_receipt_is_not_rebound_to_another_base(self):
        data = finding_fixture()
        same_head_other_base = copy.deepcopy(data["pull"])
        same_head_other_base["base_tip"] = NEXT
        publisher = SandboxPublisher(501, enabled=True)
        result = publisher.run(42, lambda: data, lambda: same_head_other_base, actor_app_id=501)
        self.assertEqual(result.reason, "evidence_changed_before_publish")
        self.assertNotIn("disposition_request", result.evidence)
        self.assertEqual(publisher.visible(HEAD).request["body"]["state"], "pending")

    def test_base_advance_requires_new_disposition_without_discarding_old_review(self):
        data = finding_fixture()
        old = attest(data, evaluate(data, 42).evidence["disposition_request"])
        self.assertTrue(evaluate(data, 42).eligible)
        data["pull"]["base_tip"] = NEXT
        data["changes"]["comparison"]["base_commit"]["sha"] = NEXT
        result = evaluate(data, 42)
        self.assertEqual(result.reason, "pr_lens_findings")
        self.assertEqual(result.evidence["disposition_request"]["base_tip"], NEXT)
        new = attest(data, result.evidence["disposition_request"])
        new["id"] = "PRR_owner_new"
        data["graph"]["pull"]["reviews"] = connection([old, new])
        self.assertTrue(evaluate(data, 42).eligible)

    def test_quoting_disposition_marker_does_not_express_acceptance(self):
        data = finding_fixture()
        payload = evaluate(data, 42).evidence["disposition_request"]
        review = attest(data, payload)
        review["body"] = "I am declining this request.\n\n```text\n" + review["body"] + "\n```"
        self.assertEqual(evaluate(data, 42).reason, "pr_lens_findings")
