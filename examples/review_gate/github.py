"""Read-only, bounded GitHub collector for the AI_CONTEXT gate pilot."""

import json
import subprocess
import time
from urllib.parse import urlencode

from .evaluator import (
    BASE_REF, REPOSITORY, WORKFLOW, WORKFLOW_ID, Blocked, positive_id, pull_scope,
    require, review_comments, rows, sha, strict_json,
)

PER_PAGE = 100
MAX_PAGES = 5
MAX_BYTES = 8 * 1024 * 1024

BOT = "login __typename ... on Bot { databaseId }"
QUERY = """
query GateEvidence($owner: String!, $repo: String!, $number: Int!, $ids: [ID!]!) {
  repository(owner: $owner, name: $repo) {
    pull: pullRequest(number: $number) {
      id headRefOid baseRefOid reviewDecision
      reviewThreads(first: 100) {
        totalCount pageInfo { hasNextPage } nodes { id isResolved }
      }
      reviews(first: 100) {
        totalCount pageInfo { hasNextPage }
        nodes { id state submittedAt lastEditedAt isMinimized commit { oid } author { BOT } }
      }
    }
  }
  comments: nodes(ids: $ids) {
    ... on IssueComment {
      id body updatedAt createdAt isMinimized lastEditedAt includesCreatedEdit
      author { BOT }
      editor { BOT }
      userContentEdits(first: 100) {
        totalCount pageInfo { hasNextPage }
        nodes { editor { BOT } editedAt deletedAt diff }
      }
    }
  }
}
""".replace("BOT", BOT)


class GitHub:
    """Fixed REST reads and a fixed GraphQL query using the local gh session."""

    def __init__(self, *, request=None):
        self.request = request or self._request
        self.deadline = time.monotonic() + 30
        self.calls = 0

    def _request(self, endpoint, body=None):
        remaining = self.deadline - time.monotonic()
        require(remaining > 0 and self.calls < 24, "read_budget_exhausted")
        self.calls += 1
        args = ["gh", "api", "--hostname", "github.com", "--method", "GET", endpoint]
        if body is not None:
            args = ["gh", "api", "--hostname", "github.com", "--method", "POST", "graphql", "--input", "-"]
        try:
            result = subprocess.run(
                args, input=None if body is None else body.encode("utf-8"),
                capture_output=True, timeout=min(15, remaining), check=True,
            )
            require(len(result.stdout) <= MAX_BYTES, "response_too_large")
            return strict_json(result.stdout.decode("utf-8"))
        except (OSError, subprocess.SubprocessError, UnicodeError, ValueError) as error:
            if isinstance(error, Blocked):
                raise
            raise Blocked("github_read_failed") from None

    def get(self, path, **query):
        suffix = f"?{urlencode(query)}" if query else ""
        return self.request(f"repos/{REPOSITORY}/{path}{suffix}")

    def pages(self, path, key=None, **query):
        items, seen, total = [], set(), None
        for page in range(1, MAX_PAGES + 1):
            data = self.get(path, per_page=PER_PAGE, page=page, **query)
            if key is not None:
                count = data["total_count"]
                require(type(count) is int and count >= 0 and total in (None, count),
                        "pagination_incomplete")
                total = count
                data = data[key]
            batch = rows(data)
            require(len(batch) <= PER_PAGE, "pagination_incomplete")
            for item in batch:
                identity = item["id"]
                require(positive_id(identity) and identity not in seen, "pagination_incomplete")
                seen.add(identity)
            items.extend(batch)
            if len(batch) < PER_PAGE or len(items) == total:
                require(total is None or len(items) == total, "pagination_incomplete")
                return items
        raise Blocked("pagination_incomplete")

    def pull(self, number):
        require(positive_id(number), "pr_identity_invalid")
        tip = self.get(f"git/ref/heads/{BASE_REF}")
        require(tip["ref"] == f"refs/heads/{BASE_REF}" and tip["object"]["type"] == "commit"
                and sha(tip["object"]["sha"]), "base_ref_invalid")
        result = self.get(f"pulls/{number}")
        return dict(result, base_tip=tip["object"]["sha"])

    def snapshot(self, number):
        pull = self.pull(number)
        scope = pull_scope(pull, number)
        head = scope["head"]
        comments = self.pages(f"issues/{number}/comments")
        selected = review_comments(comments)
        owner, repo = REPOSITORY.split("/")
        response = self.request("graphql", json.dumps({
            "query": QUERY,
            "variables": {"owner": owner, "repo": repo, "number": number,
                          "ids": [comment["node_id"] for comment in selected]},
        }))
        require(type(response) is dict and not response.get("errors"), "graphql_incomplete")
        graph = response["data"]
        return {
            "pull": pull,
            "open_pulls": self.pages("pulls", state="open", base=BASE_REF),
            "comments": comments,
            "graph": {"pull": graph["repository"]["pull"], "comments": graph["comments"]},
            "checks": self.pages(f"commits/{head}/check-runs", "check_runs", filter="latest"),
            "runs": self.pages(f"actions/workflows/{WORKFLOW_ID}/runs", "workflow_runs",
                               head_sha=head, event="pull_request"),
            "workflow_blobs": [self.get(f"contents/{WORKFLOW}", ref=ref)
                               for ref in (scope["base_tip"], head)],
        }
