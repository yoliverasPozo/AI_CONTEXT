from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Iterable, Sequence

from . import __version__


@dataclass(frozen=True)
class Adapter:
    resource: str
    destination: str
    description: str


ADAPTERS: dict[str, Adapter] = {
    "codex": Adapter("AGENTS.md", "AGENTS.md", "Codex / AGENTS.md-compatible agents"),
    "claude": Adapter("CLAUDE.md", "CLAUDE.md", "Claude Code"),
    "gemini": Adapter("GEMINI.md", "GEMINI.md", "Gemini CLI"),
    "generic": Adapter(
        "GENERIC_PROMPT.md",
        "AI_CONTEXT_PROMPT.md",
        "agents without a dedicated repository instruction file",
    ),
}

CORE_RESOURCE = "AI_CONTEXT.md"
CORE_DESTINATION = "docs/AI_CONTEXT.md"
DIRECTORIES = ("docs/decisions", "docs/sessions")


class InitError(RuntimeError):
    """Raised when initialization cannot safely continue."""


def find_git_root(start: Path) -> Path | None:
    """Return the nearest parent containing .git, including Git worktrees."""
    candidate = start.expanduser().resolve()
    if candidate.is_file():
        candidate = candidate.parent

    for path in (candidate, *candidate.parents):
        if (path / ".git").exists():
            return path
    return None


def parse_agents(value: str | None) -> list[str]:
    if value is None:
        return []

    names = [part.strip().lower() for part in value.split(",") if part.strip()]
    if not names or names == ["none"]:
        return []
    if "none" in names:
        raise InitError("'none' cannot be combined with other agent names")

    unknown = sorted(set(names) - set(ADAPTERS))
    if unknown:
        allowed = ", ".join(sorted(ADAPTERS))
        raise InitError(f"unknown agent(s): {', '.join(unknown)}; choose from: {allowed}")

    return list(dict.fromkeys(names))


def prompt_for_agents() -> list[str]:
    choices = ", ".join(ADAPTERS)
    print("Optional agent adapters:")
    for name, adapter in ADAPTERS.items():
        print(f"  {name:<7} {adapter.description}")
    answer = input(f"Agents to install [{choices}] (comma-separated, blank=none): ")
    return parse_agents(answer)


def _resource_text(name: str) -> str:
    return resources.files("ai_context.resources").joinpath(name).read_text(encoding="utf-8")


def _managed_files(agent_names: Iterable[str]) -> dict[str, str]:
    files = {CORE_DESTINATION: CORE_RESOURCE}
    for name in agent_names:
        adapter = ADAPTERS[name]
        files[adapter.destination] = adapter.resource
    return files


def initialize(
    repo_root: Path,
    agent_names: Sequence[str],
    *,
    force: bool = False,
    dry_run: bool = False,
) -> tuple[list[str], list[str]]:
    """Initialize AI_CONTEXT and return (created, overwritten) relative paths."""
    managed = _managed_files(agent_names)
    conflicts = [relative for relative in managed if (repo_root / relative).exists()]

    if conflicts and not force:
        formatted = "\n  ".join(conflicts)
        raise InitError(
            "refusing to overwrite existing managed file(s):\n"
            f"  {formatted}\n"
            "Re-run with --force only if replacing them is intentional."
        )

    created: list[str] = []
    overwritten: list[str] = []

    if not dry_run:
        for directory in DIRECTORIES:
            (repo_root / directory).mkdir(parents=True, exist_ok=True)

    for relative, resource_name in managed.items():
        destination = repo_root / relative
        existed = destination.exists()
        if not dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(_resource_text(resource_name), encoding="utf-8")
        (overwritten if existed else created).append(relative)

    return created, overwritten


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-context",
        description="Repository-native shared memory scaffolding for AI-assisted projects.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    commands = parser.add_subparsers(dest="command", required=True)
    init_parser = commands.add_parser("init", help="initialize AI_CONTEXT in a Git repository")
    init_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="path inside the target Git repository (default: current directory)",
    )
    init_parser.add_argument(
        "--agents",
        metavar="LIST",
        help="comma-separated adapters: codex,claude,gemini,generic; use none for no adapters",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite AI_CONTEXT-managed files that already exist",
    )
    init_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show what would be created without modifying the repository",
    )
    return parser


def _run_init(args: argparse.Namespace) -> int:
    start = Path(args.path)
    repo_root = find_git_root(start)
    if repo_root is None:
        raise InitError(f"no Git repository found from: {start.expanduser().resolve()}")

    if args.agents is not None:
        agent_names = parse_agents(args.agents)
    elif sys.stdin.isatty():
        agent_names = prompt_for_agents()
    else:
        agent_names = []

    created, overwritten = initialize(
        repo_root,
        agent_names,
        force=args.force,
        dry_run=args.dry_run,
    )

    prefix = "Would initialize" if args.dry_run else "AI_CONTEXT initialized"
    print(f"{prefix} in {repo_root}")

    if created:
        print("\nCreated:" if not args.dry_run else "\nWould create:")
        for path in created:
            print(f"  {path}")
    if overwritten:
        print("\nOverwritten:" if not args.dry_run else "\nWould overwrite:")
        for path in overwritten:
            print(f"  {path}")

    if not agent_names:
        print("\nNo agent adapters selected. The core memory layer is still fully initialized.")

    print("\nDirectories:")
    for directory in DIRECTORIES:
        print(f"  {directory}/")

    if not args.dry_run:
        print(
            "\nNext:\n"
            "  Ask your AI agent to inspect the repository and populate docs/AI_CONTEXT.md,\n"
            "  then maintain it together with decisions and session handoffs as the project evolves."
        )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            return _run_init(args)
    except InitError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    parser.error(f"unsupported command: {args.command}")
    return 2
