"""Check that AI_CONTEXT finds a Git worktree when .git is a file.

Unlike an ordinary clone, a linked Git worktree uses a .git pointer file.
This test exercises an existing, documented behavior without changing the CLI.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_context.cli import find_git_root


class GitWorktreeDiscoveryTests(unittest.TestCase):
    def test_nested_directory_finds_worktree_git_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".git").write_text(
                "gitdir: /example/.git/worktrees/sandbox\n",
                encoding="utf-8",
            )
            nested = root / "docs" / "sessions"
            nested.mkdir(parents=True)

            self.assertEqual(find_git_root(nested), root.resolve())

    def test_root_directory_finds_worktree_git_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".git").write_text(
                "gitdir: /example/.git/worktrees/sandbox\\n",
                encoding="utf-8",
            )

            self.assertEqual(find_git_root(root), root.resolve())

    def test_nested_file_finds_worktree_git_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".git").write_text(
                "gitdir: /example/.git/worktrees/sandbox\n",
                encoding="utf-8",
            )
            nested_file = root / "docs" / "AI_CONTEXT.md"
            nested_file.parent.mkdir(parents=True)
            nested_file.write_text("# Context\n", encoding="utf-8")

            self.assertEqual(find_git_root(nested_file), root.resolve())


if __name__ == "__main__":
    unittest.main()
