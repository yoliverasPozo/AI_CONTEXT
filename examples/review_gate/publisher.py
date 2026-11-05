"""In-memory publication model. Requests are recorded without an HTTP transport."""

from copy import deepcopy
from dataclasses import dataclass
from threading import Lock

from .evaluator import (
    ACTIONS_APP, CODEX, PR_LENS, REPO_ID, Decision, commit_status, positive_id,
    reconcile, require,
)


@dataclass(frozen=True)
class SimulatedReceipt:
    repository_id: int
    app_id: int
    generation: int
    scope: dict
    request: dict
    digest: str | None
    reason: str
    evidence: dict


class SandboxPublisher:
    """Model a commit-scoped status and a separate PR-specific receipt."""

    def __init__(self, app_id, *, enabled=False, max_writes=1000):
        self.app_id = app_id
        self.enabled = enabled is True
        self.max_writes = max_writes
        self._lock = Lock()
        self._generations = {}
        self._owners = {}
        self._visible = {}
        self._confirmed = {}
        self._writes = {}

    def visible(self, head):
        """The native status would be visible for every PR with this head."""
        with self._lock:
            return deepcopy(self._visible.get(head))

    def confirmed_for(self, decision):
        """Match an acknowledged receipt to a fresh decision, never to a SHA alone."""
        if not decision.eligible:
            return None
        head = decision.head
        with self._lock:
            receipt = self._confirmed.get(head)
            if (receipt and receipt.request["body"]["state"] == "success"
                    and receipt.scope == decision.evidence["pr"] and receipt.digest == decision.digest):
                return deepcopy(receipt)
        return None

    def run(self, number, read_snapshot, read_pull, *, actor_app_id, fault=None):
        if not self.enabled:
            return Decision("sandbox_publisher_disabled")
        if (not positive_id(self.app_id) or not positive_id(actor_app_id)
                or actor_app_id != self.app_id or self.app_id in (ACTIONS_APP, CODEX[2], PR_LENS[2])):
            return Decision("sandbox_publisher_identity_mismatch")
        if not positive_id(self.max_writes) or self.max_writes > 1000:
            return Decision("sandbox_write_bound_invalid")
        if not positive_id(number):
            return Decision("pr_identity_invalid")

        # Even an out-of-scope PR invalidates its local receipt. No native
        # status is revoked by this step, which models the external gap.
        with self._lock:
            for head, owner in self._owners.items():
                if owner[1] == number:
                    self._confirmed.pop(head, None)
                    self._generations[head] += 1
        generation = None

        def publish(head, state, decision):
            nonlocal generation
            scope = decision.evidence["pr"]
            request = commit_status(head, state, decision)
            with self._lock:
                owner = (scope["id"], scope["number"])
                if state == "pending":
                    require(self._owners.get(head, owner) == owner, "sandbox_shared_head")
                    self._owners[head] = owner
                    generation = self._generations.get(head, 0) + 1
                    self._generations[head] = generation
                require(self._generations[head] == generation, "sandbox_publication_superseded")
                self._confirmed.pop(head, None)
                require(self._writes.get(head, 0) < self.max_writes, "sandbox_status_budget_exhausted")
                if fault == (state, "before"):
                    raise OSError("simulated request failure")
                receipt = SimulatedReceipt(REPO_ID, self.app_id, generation, deepcopy(scope),
                                           request, decision.digest, decision.reason,
                                           deepcopy(decision.evidence))
                self._visible[head] = receipt
                self._writes[head] = self._writes.get(head, 0) + 1
                if fault == (state, "after"):
                    raise OSError("simulated acknowledgement loss")
                self._confirmed[head] = receipt

        return reconcile(number, read_snapshot, read_pull, publish)
