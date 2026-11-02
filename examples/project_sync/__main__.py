"""Print proposals. There is deliberately no apply or credential setup command."""
import argparse
import json
from pathlib import Path
import sys

from .planner import PlanError, plan, validate_config


def read_json(path):
    if Path(path).stat().st_size > 16 * 1024 * 1024:
        raise PlanError("JSON file exceeds 16 MiB limit")
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--snapshot")
    source.add_argument("--live", action="store_true")
    parser.add_argument("--cursor", help="Previously reviewed observed-key cursor; never updated in place")
    args = parser.parse_args(argv)
    try:
        config = validate_config(read_json(args.config))
        if args.live:
            from .collector import GhClient, collect
            snapshot = collect(config, GhClient(config["limits"]))
        else:
            snapshot = read_json(args.snapshot)
        result = plan(config, snapshot, read_json(args.cursor) if args.cursor else None)
        result["source"] = "live-read" if args.live else "offline-simulation"
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (PlanError, OSError, ValueError, KeyError, TypeError) as error:
        # Do not echo source documents, subprocess output, paths or credentials.
        message = str(error) if isinstance(error, PlanError) else "invalid or unreadable input"
        print("project-sync: " + message, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
