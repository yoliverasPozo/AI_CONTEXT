"""Evaluate authenticated GitHub evidence without running PR code."""

from dataclasses import dataclass, field
import hashlib
import json
import re

from .changes import verified_changes

REPOSITORY = "yoliverasPozo/AI_CONTEXT"
REPO_ID = 1350149746
BASE_REF = "main"
CONTEXT = "AI review complete"
WORKFLOW = ".github/workflows/tests.yml"
WORKFLOW_ID = 347167039
ACTIONS_APP = 15368
CODEX = (199175422, "chatgpt-codex-connector", 1144995)
PR_LENS = (320153949, "coldtea-pr-lens", 4690539)
DISPOSITION_OWNER = 8781658
DISPOSITION_MARKER = "ai-review-gate-disposition:v1"
LENS_SKIP = """<!-- pr-lens:sticky -->

> [!NOTE]
> Nothing here is code, only docs, data or images, so PR Lens left this pull request undrawn. Comment `@pr-lens draw` to draw it

<sub>`github.comment.notice: false` in `.github/pr-lens.yml` turns this note off</sub>"""
CI_NAMES = tuple(
    f"test ({os}, {python})"
    for os in ("ubuntu-latest", "windows-latest")
    for python in ("3.10", "3.13")
)


class Blocked(ValueError):
    """A fixed reason code, never a remote error or comment body."""


def require(condition, reason):
    if not condition:
        raise Blocked(reason)


def strict_json(text):
    def unique(pairs):
        values = {}
        for key, value in pairs:
            if key in values:
                raise ValueError("duplicate JSON key")
            values[key] = value
        return values

    def invalid_constant(_):
        raise ValueError("non-finite JSON value")

    return json.loads(text, object_pairs_hook=unique, parse_constant=invalid_constant)


def fingerprint(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def sha(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{40}", value) is not None


def positive_id(value):
    return type(value) is int and value > 0


def rows(value):
    require(type(value) is list and all(type(item) is dict for item in value), "evidence_unavailable")
    return value


def connection(value, reason):
    items = rows(value["nodes"])
    require(
        value["pageInfo"]["hasNextPage"] is False
        and type(value["totalCount"]) is int
        and value["totalCount"] == len(items),
        reason,
    )
    return items


def pull_scope(pull, number):
    """Return comparable scope fields, excluding mutable handoff metadata."""
    base, head = pull["base"], pull["head"]
    require(
        positive_id(number) and pull["number"] == number
        and pull["state"] == "open" and pull["draft"] is False
        and base["ref"] == BASE_REF
        and all(ref["repo"] and ref["repo"]["id"] == REPO_ID
                and ref["repo"]["full_name"] == REPOSITORY for ref in (base, head)),
        "pr_out_of_scope",
    )
    require(
        positive_id(pull["id"]) and isinstance(pull["node_id"], str) and pull["node_id"]
        and sha(head["sha"]) and sha(base["sha"]) and sha(pull["base_tip"])
        and isinstance(head["ref"], str) and head["ref"],
        "pr_identity_invalid",
    )
    return {
        "id": pull["id"], "node": pull["node_id"], "number": number,
        "head": head["sha"], "base": base["sha"], "base_tip": pull["base_tip"],
        "branch": head["ref"],
    }


def rest_bot(comment, identity):
    user = comment.get("user") or {}
    app = comment.get("performed_via_github_app") or {}
    bot_id, login, app_id = identity
    return user.get("id") == bot_id and user.get("type") == "Bot" and (
        user.get("login") == f"{login}[bot]" and app.get("id") == app_id
    )


def graph_bot(actor, identity):
    bot_id, login, _ = identity
    return isinstance(actor, dict) and actor.get("__typename") == "Bot" and (
        actor.get("databaseId") == bot_id and actor.get("login") == login
    )


def review_comments(comments):
    """Select the two authoritative comments before requesting edit history."""
    selected = []
    for name, identity, hint in (
        ("codex", CODEX, "codex-review-state:"),
        ("pr_lens", PR_LENS, "<!-- pr-lens:sticky -->"),
    ):
        matches = [
            item for item in rows(comments) if rest_bot(item, identity)
            and isinstance(item.get("body"), str) and hint in item["body"]
        ]
        require(len(matches) == 1, f"{name}_comment_missing_or_ambiguous")
        selected.append(matches[0])
    return selected


def comment_proof(comment, nodes, identity, name):
    reason = f"{name}_provenance_invalid"
    node_id = comment["node_id"]
    matches = [item for item in nodes if item["id"] == node_id]
    require(len(matches) == 1 and positive_id(comment["id"]), reason)
    node = matches[0]
    require(
        graph_bot(node["author"], identity) and node["isMinimized"] is False
        and node["body"] == comment["body"] and node["updatedAt"] == comment["updated_at"]
        and node["createdAt"] == comment["created_at"],
        reason,
    )
    history = connection(node["userContentEdits"], reason)
    if node["lastEditedAt"] is None:
        require(node["editor"] is None and not history and node["includesCreatedEdit"] is False, reason)
    else:
        require(
            graph_bot(node["editor"], identity) and node["includesCreatedEdit"] is True and history
            and history[0]["editedAt"] == node["lastEditedAt"]
            and history[0]["diff"] == node["body"]
            and all(graph_bot(edit["editor"], identity) and edit["deletedAt"] is None
                    and isinstance(edit["editedAt"], str) for edit in history),
            reason,
        )
    return {"id": comment["id"], "bot_id": identity[0], "app_id": identity[2],
            "sha256": fingerprint(node)}


def marker(body, prefix, reason):
    # One reserved marker on its own line. Reject duplicates and unknown syntax.
    require(body.count(prefix) == 1, reason)
    matches = re.findall(r"^<!-- " + re.escape(prefix) + r" (\{[^\r\n]*\}) -->$", body, re.M)
    require(len(matches) == 1, reason)
    try:
        value = strict_json(matches[0])
    except ValueError:
        raise Blocked(reason) from None
    require(type(value) is dict, reason)
    return value


def codex_review(body, head):
    state = marker(body, "codex-review-state:v1", "codex_marker_invalid")
    review = state.get("code_review")
    require(isinstance(review, dict) and sha(review.get("commit_sha")), "codex_incomplete")
    require(review["commit_sha"] == head, "codex_stale")
    require(review.get("status") == "completed", "codex_incomplete")
    require(
        review.get("has_any_findings") is False and review.get("has_unresolved_findings") is False,
        "codex_findings",
    )
    if "security_review" in state:
        security = state["security_review"]
        keys = {"commit_sha", "status", "has_any_findings", "has_unresolved_findings"}
        require(type(security) is dict and set(security) == keys, "codex_security_incomplete")
        if not all(value is None for value in security.values()):
            require(security["commit_sha"] == head and security["status"] == "completed"
                    and security["has_any_findings"] is False
                    and security["has_unresolved_findings"] is False, "codex_security_incomplete")


def lens_state(body, head, number):
    state = marker(body, "pr-lens:state", "pr_lens_marker_invalid")
    require(type(state.get("v")) is int and state["v"] == 1 and sha(state.get("headSha")),
            "pr_lens_marker_invalid")
    require(state["headSha"] == head and state.get("outdated", False) is False, "pr_lens_stale")
    require(state.get("graphKey") == f"graphs/{REPOSITORY}/pr/{number}/{head}.json",
            "pr_lens_marker_invalid")


def lens_section(body, outcome, reason):
    sections = re.findall(r"^\*\*Review\*\*\n\n(.*?)\n\n<br />", body, re.M | re.S)
    require(body.splitlines().count("**Review**") == 1 and sections == [outcome], reason)


def lens_review(node, head, number):
    body = node["body"]
    lens_state(body, head, number)
    short = head[:7]
    lens_section(body, f"✨ Nothing flagged · reviewed `{short}`", "pr_lens_incomplete_or_findings")

    # The check and full SHA marker are drawing evidence. Confirm that a
    # bot-authored version for that full SHA actually transitioned to clean.
    reason = "pr_lens_review_transition_unverified"
    history = node["userContentEdits"]["nodes"]
    require(len(history) >= 2 and history[0]["editedAt"] > history[1]["editedAt"]
            and all(isinstance(edit["diff"], str) for edit in history), reason)
    prior = history[1]["diff"]
    try:
        lens_state(prior, head, number)
        lens_section(prior, f"**Reviewing `{short}`** · this comment updates in place", reason)
    except Blocked:
        raise Blocked(reason) from None
    for edit in history[1:]:
        historical_heads = re.findall(r'"headSha"\s*:\s*"([0-9a-f]{40})"', edit["diff"])
        require(not any(oid != head and oid[:7] == short for oid in historical_heads), reason)
    return history[1]["editedAt"]


def review_proof(pull, head):
    reviews = connection(pull["reviews"], "reviews_incomplete")
    require(all(isinstance(review["id"], str) and review["id"] and review["author"] for review in reviews)
            and len({review["id"] for review in reviews}) == len(reviews), "reviews_incomplete")
    relevant = []
    for review in reviews:
        actor = review["author"]
        if actor.get("__typename") == "Bot":
            require(positive_id(actor.get("databaseId")), "reviews_incomplete")
        if actor.get("databaseId") not in (CODEX[0], PR_LENS[0]):
            continue
        identity = CODEX if actor["databaseId"] == CODEX[0] else PR_LENS
        commit = (review["commit"] or {}).get("oid")
        require(graph_bot(actor, identity) and sha(commit), "reviews_incomplete")
        # Observed clean reviews use sticky summaries. A separate same-head
        # bot submission might be a finding that has not reached the summary.
        require(commit != head, "reviewer_submission_requires_disposition")
        relevant.append(review)
    return fingerprint(sorted(relevant, key=lambda review: review["id"]))


def passed_check(checks, name, app_id, head, reason):
    candidates = [check for check in checks if check["name"] == name]
    require(len(candidates) == 1, reason)
    check = candidates[0]
    require(
        positive_id(check["id"]) and check["app"]["id"] == app_id
        and check["head_sha"] == head and check["status"] == "completed"
        and check["conclusion"] == "success",
        reason,
    )
    return check


def ci_proof(snapshot, scope, checks):
    blobs = rows(snapshot["workflow_blobs"])
    require(
        len(blobs) == 2 and all(blob["type"] == "file" and sha(blob["sha"]) for blob in blobs)
        and blobs[0]["sha"] == blobs[1]["sha"],
        "ci_definition_changed",
    )
    runs = rows(snapshot["runs"])
    require(runs and all(positive_id(run["run_number"]) for run in runs), "ci_run_incomplete")
    latest_number = max(run["run_number"] for run in runs)
    latest = [run for run in runs if run["run_number"] == latest_number]
    require(len(latest) == 1, "ci_run_incomplete")
    run = latest[0]
    suite = run["check_suite_id"]
    require(
        positive_id(run["id"]) and positive_id(suite)
        and run["workflow_id"] == WORKFLOW_ID and run["path"] == WORKFLOW
        and run["event"] == "pull_request" and run["head_sha"] == scope["head"]
        and run["head_branch"] == scope["branch"]
        and run["repository"]["id"] == REPO_ID and run["head_repository"]["id"] == REPO_ID
        and run["status"] == "completed" and run["conclusion"] == "success",
        "ci_run_incomplete",
    )
    jobs = [passed_check(checks, name, ACTIONS_APP, scope["head"], "ci_checks_incomplete")
            for name in CI_NAMES]
    require(all(job["check_suite"]["id"] == suite for job in jobs), "ci_checks_incomplete")
    return {"workflow_blob": blobs[0]["sha"], "run": run["id"], "suite": suite,
            "jobs": [job["id"] for job in jobs], "sha256": fingerprint([run, jobs])}


def intentional_skip(snapshot, scope, lens, lens_proof, reviews, checks, proof):
    require(not any(check["name"] == "PR Lens" or check["app"]["id"] == PR_LENS[2]
                    for check in checks), "pr_lens_skip_contradicts_check")
    require(not any(comment["id"] != lens["id"] for comment in snapshot["comments"]
                    if rest_bot(comment, PR_LENS)), "pr_lens_skip_history_ambiguous")
    try:
        category, merge_base, entries = verified_changes(
            snapshot["changes"], scope, snapshot["pull"]["changed_files"],
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        raise Blocked("change_evidence_invalid") from None
    proof["pr_lens_outcome"] = "intentional_skip"
    proof["changes"] = {"class": category, "merge_base": merge_base,
                        "files": snapshot["pull"]["changed_files"], "sha256": fingerprint(entries)}
    if category == "executable_or_mixed":
        return "pr_lens_skip_not_permitted"
    require(snapshot["pull"]["base"]["repo"]["owner"]["id"] == DISPOSITION_OWNER,
            "disposition_owner_unverified")

    request = {
        "decision": "accept_intentional_skip", "repository_id": REPO_ID,
        "pr_id": scope["id"], "pr_number": scope["number"], "target_branch": BASE_REF,
        "head": scope["head"], "base_tip": scope["base_tip"], "merge_base": merge_base,
        "change_class": category, "files_sha256": proof["changes"]["sha256"],
        "notice_id": lens_proof["id"], "notice_sha256": lens_proof["sha256"],
    }
    candidates = []
    for review in reviews:
        body = review.get("body")
        if (review["author"].get("databaseId") != DISPOSITION_OWNER
                or (review["commit"] or {}).get("oid") != scope["head"]
                or not isinstance(body, str) or DISPOSITION_MARKER not in body):
            continue
        submitted_request = marker(body, DISPOSITION_MARKER, "skip_disposition_invalid")
        require(set(submitted_request) == set(request), "skip_disposition_invalid")
        # Preserve old reviews in the audit trail. An older base, diff or
        # notice may require a new disposition for the same head.
        if submitted_request == request:
            candidates.append(review)
    if not candidates:
        proof["disposition_request"] = request
        return "pr_lens_skip_requires_disposition"
    require(len(candidates) == 1, "skip_disposition_invalid")
    review = candidates[0]
    submitted = review["submittedAt"]
    require(
        review["author"]["__typename"] == "User" and review["state"] == "COMMENTED"
        and isinstance(submitted, str) and submitted > lens["updated_at"]
        and review["lastEditedAt"] is None and review["editor"] is None
        and review["isMinimized"] is False and review["includesCreatedEdit"] is False
        and not connection(review["userContentEdits"], "skip_disposition_invalid"),
        "skip_disposition_invalid",
    )
    proof["disposition"] = {"review": review["id"], "actor_id": DISPOSITION_OWNER,
                            "sha256": fingerprint(review), "scope": request}
    return "eligible"


def verify_lifecycle(timeline):
    # GitHub reports the total count of all timeline items even when itemTypes
    # filters the nodes. Only an empty, terminal filtered page proves absence.
    events = rows(timeline["nodes"])
    require(not events, "pr_lifecycle_requires_revalidation")
    require(type(timeline["totalCount"]) is int and timeline["totalCount"] >= 0
            and timeline["pageInfo"]["hasNextPage"] is False, "pr_lifecycle_unavailable")


@dataclass(frozen=True)
class Decision:
    reason: str
    head: str | None = None
    digest: str | None = None
    evidence: dict = field(default_factory=dict)

    @property
    def eligible(self):
        return self.reason == "eligible"


def evaluate(snapshot, number):
    try:
        scope = pull_scope(snapshot["pull"], number)
        head = scope["head"]
        same_head = [
            (pr["id"], pr["number"]) for pr in rows(snapshot["open_pulls"])
            if pr["head"]["sha"] == head
        ]
        require(same_head == [(scope["id"], number)], "ambiguous_head")

        graph = snapshot["graph"]
        pull = graph["pull"]
        require(pull["id"] == scope["node"] and pull["headRefOid"] == head
                and pull["baseRefOid"] == scope["base"], "pr_changed_during_read")
        require(pull["reviewDecision"] in (None, "APPROVED", "REVIEW_REQUIRED"),
                "blocking_review_decision")
        verify_lifecycle(pull["lifecycle"])
        threads = connection(pull["reviewThreads"], "review_threads_incomplete")
        require(all(thread["isResolved"] is True for thread in threads), "unresolved_review_thread")
        require(all(isinstance(thread["id"], str) and thread["id"] for thread in threads)
                and len({thread["id"] for thread in threads}) == len(threads), "review_threads_incomplete")
        reviews_digest = review_proof(pull, head)

        codex, lens = review_comments(snapshot["comments"])
        nodes = rows(graph["comments"])
        codex_proof = comment_proof(codex, nodes, CODEX, "codex")
        lens_proof = comment_proof(lens, nodes, PR_LENS, "pr_lens")
        codex_review(codex["body"], head)
        checks = rows(snapshot["checks"])
        proof = {
            "pr": scope, "codex": codex_proof, "pr_lens": lens_proof,
            "review_decision": pull["reviewDecision"], "review_submissions_sha256": reviews_digest,
            "threads": sorted(t["id"] for t in threads),
        }
        if lens["body"].rstrip("\n") == LENS_SKIP:
            lens_node = next(node for node in nodes if node["id"] == lens["node_id"])
            require(lens_node["lastEditedAt"] is None, "pr_lens_skip_history_ambiguous")
            proof["ci"] = ci_proof(snapshot, scope, checks)
            reason = intentional_skip(snapshot, scope, lens, lens_proof,
                                      pull["reviews"]["nodes"], checks, proof)
            return Decision(reason, head, fingerprint(proof), proof)

        lens_node = next(node for node in nodes if node["id"] == lens["node_id"])
        lens_pending_at = lens_review(lens_node, head, number)
        lens_check = passed_check(checks, "PR Lens", PR_LENS[2], head, "pr_lens_check_incomplete")
        require(
            lens_check["details_url"] == f"https://github.com/{REPOSITORY}/pull/{number}"
            f"#issuecomment-{lens['id']}",
            "pr_lens_check_not_linked",
        )
        require(lens_check["completed_at"] == lens_pending_at, "pr_lens_check_transition_mismatch")
        proof["pr_lens_outcome"] = "reviewed_clean"
        proof["pr_lens_check"] = {"id": lens_check["id"], "sha256": fingerprint(lens_check)}
        proof["ci"] = ci_proof(snapshot, scope, checks)
        return Decision("eligible", head, fingerprint(proof), proof)
    except Blocked as error:
        return Decision(error.args[0])
    except (AttributeError, KeyError, TypeError, ValueError):
        return Decision("evidence_unavailable")


def reconcile(number, read_snapshot, read_pull, publish=None):
    """Optional publication is a test seam. The read-only CLI supplies no writer."""
    try:
        if publish is not None:
            scope = pull_scope(read_pull(), number)
            publish(scope["head"], "pending",
                    Decision("evaluation_started", scope["head"], evidence={"pr": scope}))
        initial = evaluate(read_snapshot(), number)
        if publish is None:
            if (initial.eligible or "disposition_request" in initial.evidence) and (
                pull_scope(read_pull(), number) != initial.evidence["pr"]
            ):
                return Decision("evidence_changed_during_evaluation")
            return initial

        if initial.evidence.get("pr", scope) != scope:
            return Decision("evidence_changed_before_publish")
        result = initial
        if initial.eligible:
            result = evaluate(read_snapshot(), number)
            if result.evidence.get("pr", scope) != scope:
                return Decision("evidence_changed_before_publish")
            if result.eligible and result.digest != initial.digest:
                result = Decision("evidence_changed_before_publish")
        if pull_scope(read_pull(), number) != scope:
            return Decision("evidence_changed_before_publish")
        if result.eligible:
            publish(scope["head"], "success", result)
        else:
            publish(scope["head"], "failure", Decision(
                result.reason, scope["head"], result.digest, {**result.evidence, "pr": scope},
            ))
        return result
    except Blocked as error:
        return Decision(error.args[0])
    except Exception:
        # A failed read or transport must never produce a successful decision.
        return Decision("evaluation_or_publication_failed")


def commit_status(sha_value, state, decision):
    """Construct a fixed GitHub REST request for a separately trusted publisher."""
    require(sha(sha_value) and decision.head == sha_value, "status_scope_invalid")
    require(
        (state == "success" and decision.eligible and isinstance(decision.digest, str)
         and re.fullmatch(r"[a-f0-9]{64}", decision.digest))
        or (state == "pending" and decision.reason == "evaluation_started")
        or (state == "failure" and not decision.eligible and decision.reason != "evaluation_started"),
        "status_state_invalid",
    )
    descriptions = {"pending": "Evaluation started", "failure": "Review gate blocked"}
    description = f"Evidence {decision.digest[:32]}" if state == "success" else descriptions[state]
    return {
        "method": "POST", "path": f"repos/{REPOSITORY}/statuses/{sha_value}",
        "body": {"context": CONTEXT, "state": state, "description": description},
    }


def event_candidates(events):
    """Coalesce a batch of webhook hints. Each selected PR needs fresh reads."""
    numbers = set()
    for event, payload in events:
        action = payload.get("action")
        if event == "issue_comment":
            issue = payload.get("issue", {})
            author = payload.get("comment", {}).get("user", {}).get("id")
            if ("pull_request" in issue and author in (CODEX[0], PR_LENS[0])
                    and action in ("created", "edited", "deleted")):
                numbers.add(issue.get("number"))
        elif event in ("pull_request", "pull_request_target"):
            if action in (
                "opened", "reopened", "synchronize", "ready_for_review", "converted_to_draft", "closed",
            ) or (action == "edited" and "base" in payload.get("changes", {})):
                numbers.add(payload.get("number"))
        elif event in ("pull_request_review", "pull_request_review_comment", "pull_request_review_thread"):
            numbers.add(payload.get("pull_request", {}).get("number"))
        elif event == "check_run" and action == "completed":
            check = payload.get("check_run", {})
            if check.get("name") == "PR Lens" and check.get("app", {}).get("id") == PR_LENS[2]:
                numbers.update(pr.get("number") for pr in check.get("pull_requests", []))
        elif event == "workflow_run" and action == "completed":
            run = payload.get("workflow_run", {})
            if run.get("workflow_id") == WORKFLOW_ID and run.get("event") == "pull_request":
                numbers.update(pr.get("number") for pr in run.get("pull_requests", []))
    return tuple(sorted(number for number in numbers if positive_id(number)))
