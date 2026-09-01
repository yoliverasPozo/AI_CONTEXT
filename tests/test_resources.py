from __future__ import annotations

import unittest
from importlib import resources
from pathlib import Path


class ResourceSyncTests(unittest.TestCase):
    def test_bundled_resources_match_canonical_repository_files(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        mappings = {
            "AI_CONTEXT.md": repo_root / "templates" / "AI_CONTEXT.md",
            "AGENTS.md": repo_root / "examples" / "AGENTS.md",
            "CLAUDE.md": repo_root / "examples" / "CLAUDE.md",
            "GEMINI.md": repo_root / "examples" / "GEMINI.md",
            "GENERIC_PROMPT.md": repo_root / "examples" / "GENERIC_PROMPT.md",
        }

        for resource_name, canonical_path in mappings.items():
            with self.subTest(resource=resource_name):
                bundled = (
                    resources.files("ai_context.resources")
                    .joinpath(resource_name)
                    .read_text(encoding="utf-8")
                )
                canonical = canonical_path.read_text(encoding="utf-8")
                self.assertEqual(bundled, canonical)


if __name__ == "__main__":
    unittest.main()
