from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ai_context.cli import InitError, find_git_root, initialize, parse_agents


class InitTests(unittest.TestCase):
    def make_repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / ".git").mkdir()
        return temp, root

    def test_find_git_root_from_nested_directory(self) -> None:
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        nested = root / "a" / "b"
        nested.mkdir(parents=True)
        self.assertEqual(find_git_root(nested), root.resolve())

    def test_initialize_core_and_selected_adapters(self) -> None:
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)

        created, overwritten = initialize(root, ["codex", "claude"])

        self.assertEqual(overwritten, [])
        self.assertEqual(
            set(created),
            {"docs/AI_CONTEXT.md", "AGENTS.md", "CLAUDE.md"},
        )
        self.assertTrue((root / "docs/AI_CONTEXT.md").is_file())
        self.assertTrue((root / "docs/decisions").is_dir())
        self.assertTrue((root / "docs/sessions").is_dir())
        self.assertTrue((root / "AGENTS.md").is_file())
        self.assertTrue((root / "CLAUDE.md").is_file())
        self.assertFalse((root / "GEMINI.md").exists())

    def test_initialize_without_agents_is_vendor_neutral(self) -> None:
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)

        initialize(root, [])

        self.assertTrue((root / "docs/AI_CONTEXT.md").exists())
        self.assertFalse((root / "AGENTS.md").exists())
        self.assertFalse((root / "CLAUDE.md").exists())
        self.assertFalse((root / "GEMINI.md").exists())
        self.assertFalse((root / "AI_CONTEXT_PROMPT.md").exists())

    def test_existing_managed_file_aborts_before_any_write(self) -> None:
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        (root / "AGENTS.md").write_text("custom\n", encoding="utf-8")

        with self.assertRaises(InitError):
            initialize(root, ["codex"])

        self.assertEqual((root / "AGENTS.md").read_text(encoding="utf-8"), "custom\n")
        self.assertFalse((root / "docs/AI_CONTEXT.md").exists())
        self.assertFalse((root / "docs/decisions").exists())

    def test_force_overwrites_only_managed_files(self) -> None:
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        (root / "AGENTS.md").write_text("custom\n", encoding="utf-8")
        (root / "KEEP.txt").write_text("keep\n", encoding="utf-8")

        created, overwritten = initialize(root, ["codex"], force=True)

        self.assertIn("docs/AI_CONTEXT.md", created)
        self.assertEqual(overwritten, ["AGENTS.md"])
        self.assertNotEqual((root / "AGENTS.md").read_text(encoding="utf-8"), "custom\n")
        self.assertEqual((root / "KEEP.txt").read_text(encoding="utf-8"), "keep\n")

    def test_dry_run_does_not_modify_repository(self) -> None:
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)

        created, overwritten = initialize(root, ["gemini"], dry_run=True)

        self.assertEqual(set(created), {"docs/AI_CONTEXT.md", "GEMINI.md"})
        self.assertEqual(overwritten, [])
        self.assertFalse((root / "docs").exists())
        self.assertFalse((root / "GEMINI.md").exists())

    def test_parse_agents_deduplicates_and_preserves_order(self) -> None:
        self.assertEqual(parse_agents("gemini,codex,gemini"), ["gemini", "codex"])

    def test_coordination_is_opt_in(self) -> None:
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        created, overwritten = initialize(root, [])
        self.assertEqual(created, ["docs/AI_CONTEXT.md"])
        self.assertEqual(overwritten, [])
        self.assertFalse((root / "docs/COORDINATION.md").exists())
        self.assertFalse((root / "docs/HANDOFF_TEMPLATE.md").exists())

    def test_initialize_optional_coordination(self) -> None:
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        created, overwritten = initialize(root, [], coordination=True)
        self.assertEqual(set(created), {
            "docs/AI_CONTEXT.md", "docs/COORDINATION.md", "docs/HANDOFF_TEMPLATE.md",
        })
        self.assertEqual(overwritten, [])
        for name in created:
            self.assertTrue((root / name).read_text(encoding="utf-8").strip())

    def test_work_adapter_includes_shared_protocol(self) -> None:
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        agents = parse_agents("work,codex,work")
        self.assertEqual(agents, ["work", "codex"])
        created, overwritten = initialize(root, agents)
        self.assertEqual(set(created), {
            "docs/AI_CONTEXT.md", "docs/COORDINATION.md", "docs/HANDOFF_TEMPLATE.md",
            "AI_CONTEXT_WORK.md", "AGENTS.md",
        })
        self.assertEqual(overwritten, [])
        for name in created:
            self.assertTrue((root / name).read_text(encoding="utf-8").strip())

    def test_coordination_conflicts_abort_before_any_write(self) -> None:
        for conflict in ("docs/COORDINATION.md", "docs/HANDOFF_TEMPLATE.md", "AI_CONTEXT_WORK.md"):
            with self.subTest(conflict=conflict):
                temp, root = self.make_repo()
                self.addCleanup(temp.cleanup)
                path = root / conflict
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("custom\n", encoding="utf-8")
                with self.assertRaises(InitError):
                    initialize(root, ["work", "codex"])
                self.assertEqual(path.read_text(encoding="utf-8"), "custom\n")
                self.assertFalse((root / "docs/AI_CONTEXT.md").exists())
                self.assertFalse((root / "AGENTS.md").exists())

    def test_work_dry_run_does_not_write_supporting_files(self) -> None:
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        created, overwritten = initialize(root, ["work"], dry_run=True)
        self.assertEqual(set(created), {
            "docs/AI_CONTEXT.md", "docs/COORDINATION.md", "docs/HANDOFF_TEMPLATE.md",
            "AI_CONTEXT_WORK.md",
        })
        self.assertEqual(overwritten, [])
        self.assertEqual({p.name for p in root.iterdir()}, {".git"})

    def test_coordination_force_preserves_unselected_adapters_and_sessions(self) -> None:
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        initialize(root, ["work", "codex"])
        (root / "AGENTS.md").write_text("custom agent\n", encoding="utf-8")
        session = root / "docs/sessions/2026-10-26-existing.md"
        session.write_text("existing session\n", encoding="utf-8")
        created, overwritten = initialize(root, [], coordination=True, force=True)
        self.assertEqual(created, [])
        self.assertEqual(set(overwritten), {
            "docs/AI_CONTEXT.md", "docs/COORDINATION.md", "docs/HANDOFF_TEMPLATE.md",
        })
        self.assertEqual((root / "AGENTS.md").read_text(encoding="utf-8"), "custom agent\n")
        self.assertEqual(session.read_text(encoding="utf-8"), "existing session\n")
        self.assertTrue((root / "AI_CONTEXT_WORK.md").is_file())

    def test_cli_coordination_flag_and_work_selection(self) -> None:
        for args in (["--coordination", "--agents", "none"], ["--agents", "work"]):
            with self.subTest(args=args):
                temp, root = self.make_repo()
                self.addCleanup(temp.cleanup)
                result = subprocess.run(
                    [sys.executable, "-m", "ai_context", "init", str(root), *args],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((root / "docs/COORDINATION.md").is_file())
                self.assertTrue((root / "docs/HANDOFF_TEMPLATE.md").is_file())
                self.assertEqual((root / "AI_CONTEXT_WORK.md").exists(), "work" in args)

    def test_parse_agents_accepts_none(self) -> None:
        self.assertEqual(parse_agents("none"), [])

    def test_parse_agents_rejects_unknown(self) -> None:
        with self.assertRaises(InitError):
            parse_agents("codex,unknown")

    def test_parse_agents_rejects_none_mixed_with_agent(self) -> None:
        with self.assertRaises(InitError):
            parse_agents("none,codex")


if __name__ == "__main__":
    unittest.main()
