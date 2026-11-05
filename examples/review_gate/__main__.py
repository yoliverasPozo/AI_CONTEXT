"""Read-only AI review gate CLI."""

import argparse
from dataclasses import asdict
import json

from .evaluator import CONTEXT, REPOSITORY, reconcile
from .github import GitHub


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", type=int, required=True)
    args = parser.parse_args(argv)
    api = GitHub()
    decision = reconcile(args.pr, lambda: api.snapshot(args.pr), lambda: api.pull(args.pr))
    print(json.dumps({
        **asdict(decision), "eligible": decision.eligible, "context": CONTEXT,
        "repository": REPOSITORY, "pull_request": args.pr, "mode": "observe",
        "api_calls": api.calls,
    }, sort_keys=True))
    return 0 if decision.eligible else 1


if __name__ == "__main__":
    raise SystemExit(main())
