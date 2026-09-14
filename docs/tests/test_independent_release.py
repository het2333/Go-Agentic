import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


MODULE_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(os.environ.get("GO_AGENTIC_RELEASE_ROOT", MODULE_ROOT)).resolve()
ALLOWLIST = ROOT / "tools" / "independent_release" / "release_allowlist.txt"
FORBIDDEN = ROOT / "tools" / "independent_release" / "forbidden_paths.txt"
CC_BY_4_SHA256 = "9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411"
APACHE_2_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"


def tracked_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [path for path in result.stdout.split("\0") if path]


def is_standalone_clean_release(root: Path) -> bool:
    commit_count = subprocess.run(
        ["git", "rev-list", "--count", "--all"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    roots = subprocess.run(
        ["git", "rev-list", "--max-parents=0", "--all"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    return commit_count == "1" and len(roots) == 1


class IndependentReleaseTests(unittest.TestCase):
    def test_standalone_clean_release_rejects_process_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            clean_root = Path(directory)
            (clean_root / "docs/superpowers").mkdir(parents=True)
            (clean_root / ".superpowers").mkdir()
            (clean_root / "tools/independent_release").mkdir(parents=True)
            (clean_root / "docs/superpowers/plan.md").write_text("internal plan\n", encoding="utf-8")
            (clean_root / ".superpowers/report.md").write_text("internal report\n", encoding="utf-8")
            for source in (ALLOWLIST, FORBIDDEN):
                (clean_root / "tools/independent_release" / source.name).write_bytes(source.read_bytes())
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=clean_root, check=True)
            subprocess.run(["git", "config", "user.name", "Release Test"], cwd=clean_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "release-test@example.invalid"],
                cwd=clean_root,
                check=True,
            )
            subprocess.run(["git", "add", "."], cwd=clean_root, check=True)
            subprocess.run(["git", "commit", "-qm", "clean root fixture"], cwd=clean_root, check=True)

            environment = os.environ.copy()
            environment["GO_AGENTIC_RELEASE_ROOT"] = str(clean_root)
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "unittest",
                    "docs.tests.test_independent_release.IndependentReleaseTests.test_forbidden_release_paths_are_absent",
                    "docs.tests.test_independent_release.IndependentReleaseTests.test_release_tree_matches_allowlist_roots",
                    "-v",
                ],
                cwd=MODULE_ROOT,
                env=environment,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("docs/superpowers/plan.md", result.stdout + result.stderr)
            self.assertIn(".superpowers/report.md", result.stdout + result.stderr)

    def test_dual_license_boundary(self):
        root_license_path = ROOT / "LICENSE"
        self.assertTrue(root_license_path.is_file(), "LICENSE")
        root_license = root_license_path.read_text(encoding="utf-8")
        self.assertIn("Documentation and original visual assets: CC BY 4.0", root_license)
        self.assertIn("Code under code/go-agentic: Apache License 2.0", root_license)

        cc_paths = (
            ROOT / "LICENSES" / "CC-BY-4.0.txt",
            ROOT / "docs" / "LICENSE-CC-BY-4.0.txt",
        )
        apache_paths = (
            ROOT / "LICENSES" / "Apache-2.0.txt",
            ROOT / "code" / "go-agentic" / "LICENSE",
        )
        for path in (*cc_paths, *apache_paths):
            self.assertTrue(path.is_file(), path.relative_to(ROOT))
            self.assertIn(path.relative_to(ROOT).as_posix(), root_license)

        cc_bytes = [path.read_bytes() for path in cc_paths]
        apache_bytes = [path.read_bytes() for path in apache_paths]
        self.assertEqual(cc_bytes[0], cc_bytes[1])
        self.assertEqual(apache_bytes[0], apache_bytes[1])
        for content in cc_bytes:
            self.assertEqual(hashlib.sha256(content).hexdigest(), CC_BY_4_SHA256)
        for content in apache_bytes:
            self.assertEqual(hashlib.sha256(content).hexdigest(), APACHE_2_SHA256)
            self.assertEqual(len(content), 11_358)
            self.assertEqual(len(content.splitlines()), 202)

        expected_scope_rows = (
            "| `README.md` | CC BY 4.0 |",
            "| `README_EN.md` | CC BY 4.0 |",
            "| `docs/**/*.md` | CC BY 4.0 |",
            "| `docs/assets/visuals/**` | CC BY 4.0 |",
            "| Original Mermaid and SVG embedded in documentation | CC BY 4.0 |",
            "| `code/go-agentic/**` | Apache License 2.0 |",
            "| `tools/independent_release/**` | Apache License 2.0 |",
            "| `docs/tests/**` | Apache License 2.0 |",
            "| `docs/index.html` | Apache License 2.0 |",
        )
        for row in expected_scope_rows:
            self.assertIn(row, root_license)
        self.assertIn(
            "Legal-text files are reproduced license instruments, not governed course content.",
            root_license,
        )

    def test_bilingual_readmes_summarize_the_same_license_boundary(self):
        readmes = {
            "zh": (ROOT / "README.md").read_text(encoding="utf-8"),
            "en": (ROOT / "README_EN.md").read_text(encoding="utf-8"),
        }
        for text in readmes.values():
            self.assertIn("CC BY 4.0", text)
            self.assertIn("Apache License 2.0", text)
            self.assertIn("(./LICENSE)", text)
            for path in (
                "code/go-agentic/",
                "tools/independent_release/",
                "docs/tests/",
                "docs/index.html",
            ):
                self.assertIn(path, text)

    def test_source_pages_disclose_sources_without_adaptation_positioning(self):
        source_pages = {
            "zh": (ROOT / "docs" / "来源与致谢.md").read_text(encoding="utf-8"),
            "en": (ROOT / "docs" / "Sources-and-Acknowledgements.md").read_text(
                encoding="utf-8"
            ),
        }
        required_disclosures = (
            "Pi",
            "DeepSeek Harness",
            "Hermes Agent",
            "agentic-ai-guide-zh-v1.1.0.pdf",
        )
        for text in source_pages.values():
            for disclosure in required_disclosures:
                self.assertIn(disclosure, text)
            for link in (
                "(../LICENSE)",
                "(./LICENSE-CC-BY-4.0.txt)",
                "(../LICENSES/CC-BY-4.0.txt)",
                "(../code/go-agentic/LICENSE)",
                "(../LICENSES/Apache-2.0.txt)",
            ):
                self.assertIn(link, text)

        for phrase in ("adapted from", "adaptation", "upstream"):
            self.assertNotIn(phrase, source_pages["en"].casefold())
        for phrase in ("改编自", "改编版", "上游"):
            self.assertNotIn(phrase, source_pages["zh"])

    def test_forbidden_release_paths_are_absent(self):
        forbidden = [line.strip() for line in FORBIDDEN.read_text().splitlines() if line.strip()]
        if is_standalone_clean_release(ROOT):
            forbidden.append(".superpowers")
        else:
            forbidden.remove("docs/superpowers")  # Internal plans remain runnable in source.
        tracked = tracked_paths(ROOT)
        violations = [
            path
            for path in tracked
            if any(path == prefix or path.startswith(prefix + "/") for prefix in forbidden)
        ]
        assert not violations, violations

    def test_release_tree_matches_allowlist_roots(self):
        allowed = [line.strip() for line in ALLOWLIST.read_text().splitlines() if line.strip()]
        tracked = tracked_paths(ROOT)
        if not is_standalone_clean_release(ROOT):
            tracked = [
                path
                for path in tracked
                if path != ".superpowers" and not path.startswith(".superpowers/")
            ]
        unexpected = [
            path
            for path in tracked
            if not any(path == root or path.startswith(root + "/") for root in allowed)
        ]
        assert unexpected == []


if __name__ == "__main__":
    unittest.main()
