from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.independent_release.audit_originality import (
    AuditFinding,
    audit_markdown,
    audit_repository,
    audit_text,
    chinese_ngrams,
    english_ngrams,
    normalize_markdown,
    publication_markdown_paths,
    render_json_report,
    render_markdown_report,
    validate_allowlist,
)


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "independent_release" / "audit_originality.py"


def run_git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class TextAuditTests(unittest.TestCase):
    def test_finds_twenty_character_chinese_match(self):
        source = "智能体需要在执行过程中持续观察环境并验证结果"
        findings = audit_text(source, source, zh_chars=20, en_words=12)
        self.assertTrue(any(item.kind == "chinese_run" for item in findings))

    def test_finds_twelve_word_english_match(self):
        source = "an agent must observe the environment choose an action and verify the result"
        findings = audit_text(source, source, zh_chars=20, en_words=12)
        self.assertTrue(any(item.kind == "english_run" for item in findings))

    def test_ngrams_do_not_cross_run_boundaries(self):
        self.assertEqual(chinese_ngrams("甲" * 10 + " stop " + "乙" * 10), set())
        self.assertEqual(
            english_ngrams("one two three. four five six", size=4),
            set(),
        )

    def test_chinese_ngrams_ignore_spacing_and_nonterminal_punctuation(self):
        source = "甲" * 10 + "，  " + "乙" * 10
        self.assertEqual(chinese_ngrams(source), {"甲" * 10 + "乙" * 10})

    def test_markdown_noise_does_not_create_prose_findings(self):
        current = """Visible words stay distinct.

```python
an agent must observe the environment choose an action and verify the result
```

`an agent must observe the environment choose an action and verify the result`

https://example.com/an/agent/must/observe/the/environment/choose/an/action/and/verify/the/result
"""
        upstream = current.replace("Visible words stay distinct", "Different prose remains here")
        self.assertEqual(audit_markdown(current, upstream, []), [])

    def test_markdown_punctuation_and_whitespace_normalize_without_crossing_sentences(self):
        current = "**智能体需要** 在执行过程中持续观察环境，并验证结果。另一个句子完全不同。"
        upstream = "智能体需要在执行过程中持续观察环境并验证结果。这里没有同样的后一句。"
        findings = audit_text(current, upstream, zh_chars=20, en_words=12)
        chinese = [item for item in findings if item.kind == "chinese_run"]
        self.assertEqual(len(chinese), 1)
        self.assertEqual(chinese[0].location, "line 1")
        self.assertNotIn("另一个句子", chinese[0].excerpt)

    def test_chinese_audit_does_not_cross_embedded_english_boundary(self):
        source = "甲" * 10 + " embedded English boundary " + "乙" * 10
        findings = audit_text(source, source, zh_chars=20, en_words=100)
        self.assertFalse(any(item.kind == "chinese_run" for item in findings))

    def test_english_audit_does_not_cross_embedded_chinese_boundary(self):
        source = "one two three four five six 中文边界 seven eight nine ten eleven twelve"
        findings = audit_text(source, source, zh_chars=100, en_words=12)
        self.assertFalse(any(item.kind == "english_run" for item in findings))

    def test_exact_non_code_sentence_records_current_line(self):
        current = "A short introduction.\nThis complete prose sentence is shared exactly."
        upstream = "Other opening words.\nThis complete prose sentence is shared exactly."
        findings = audit_text(current, upstream)
        exact = [item for item in findings if item.kind == "exact_sentence"]
        self.assertEqual([(item.excerpt, item.location) for item in exact], [
            ("This complete prose sentence is shared exactly", "line 2")
        ])

    def test_multiline_html_comment_preserves_following_prose_location(self):
        source = """<!--
hidden comment line
another hidden line
-->
This complete prose sentence is shared exactly.
"""
        findings = audit_text(source, source)
        exact = [item for item in findings if item.kind == "exact_sentence"]
        self.assertEqual([(item.excerpt, item.location) for item in exact], [
            ("This complete prose sentence is shared exactly", "line 5")
        ])

    def test_normalized_long_fragment_ignores_markdown_punctuation_and_spacing(self):
        words = "one two three four five six seven eight nine ten eleven"
        current = f"**{words.replace(' ', '  ')}**"
        upstream = words
        findings = audit_text(current, upstream, zh_chars=100, en_words=100)
        self.assertTrue(any(item.kind == "normalized_fragment" for item in findings))

    def test_structural_similarity_detects_matching_heading_and_step_sequences(self):
        current = """# Observe
Fresh explanation alpha.
## Decide
Fresh explanation beta.
1. inspect a new signal
2. choose a new action
3. verify a new result
"""
        upstream = """# Observe
Legacy wording gamma.
## Decide
Legacy wording delta.
1. inspect an old signal
2. choose an old action
3. verify an old result
"""
        findings = audit_text(current, upstream, zh_chars=100, en_words=100)
        self.assertTrue(any(item.kind == "structural_similarity" for item in findings))

    def test_unrelated_numbered_lists_are_not_structurally_similar(self):
        current = """1. inspect a signal
2. choose an action
3. verify the result
"""
        upstream = """1. prepare fresh vegetables
2. heat the cooking pan
3. serve dinner immediately
"""
        findings = audit_text(current, upstream, zh_chars=100, en_words=100)
        self.assertFalse(any(item.kind == "structural_similarity" for item in findings))

    def test_url_only_numbered_lists_do_not_create_structural_similarity(self):
        source = """1. https://example.com/observe/browser/state
2. https://example.com/decide/policy/evidence
3. https://example.com/verify/final/result
"""
        findings = audit_text(source, source, zh_chars=100, en_words=100)
        self.assertFalse(any(item.kind == "structural_similarity" for item in findings))

    def test_inline_code_only_numbered_lists_do_not_create_structural_similarity(self):
        source = """1. `observe browser state`
2. `decide policy evidence`
3. `verify final result`
"""
        findings = audit_text(source, source, zh_chars=100, en_words=100)
        self.assertFalse(any(item.kind == "structural_similarity" for item in findings))

    def test_paragraph_order_requires_matching_content_in_the_same_sequence(self):
        topics = [
            "observation browser state",
            "decision policy evidence",
            "action tool permission",
            "verification expected result",
            "memory retrieval source",
            "context budget selection",
            "failure retry limit",
            "completion final artifact",
        ]
        current = "\n\n".join(f"Current explanation covers {topic}." for topic in topics)
        same_order = "\n\n".join(f"Legacy discussion describes {topic}." for topic in topics)
        reverse_order = "\n\n".join(
            f"Legacy discussion describes {topic}." for topic in reversed(topics)
        )
        self.assertTrue(any(
            item.kind == "structural_similarity"
            for item in audit_text(current, same_order, zh_chars=100, en_words=100)
        ))
        self.assertFalse(any(
            item.kind == "structural_similarity"
            for item in audit_text(current, reverse_order, zh_chars=100, en_words=100)
        ))

    def test_allowlist_is_exactly_scoped_by_path_and_excerpt(self):
        sentence = "This complete prose sentence is shared exactly"
        entries = [{
            "current_path": "docs/chapter1/en.md",
            "excerpt": sentence,
            "reason": "Quoted definition with source attribution.",
        }]
        self.assertEqual(
            audit_markdown(
                sentence + ".",
                sentence + ".",
                entries,
                current_path="docs/chapter1/en.md",
            ),
            [],
        )
        self.assertTrue(audit_markdown(
            sentence + ".",
            sentence + ".",
            entries,
            current_path="docs/chapter2/en.md",
        ))

    def test_allowlist_rejects_missing_fields_and_global_wildcards(self):
        with self.assertRaisesRegex(ValueError, "current_path, excerpt, and reason"):
            validate_allowlist([{"excerpt": "text", "reason": "because"}])
        with self.assertRaisesRegex(ValueError, "literal current_path"):
            validate_allowlist([{
                "current_path": "*",
                "excerpt": "text",
                "reason": "because",
            }])

    def test_publication_surface_has_fifty_chapters_and_twelve_front_or_back_matter_files(self):
        paths = publication_markdown_paths(ROOT)
        chapters = [path for path in paths if path.startswith("docs/chapter")]
        other = [path for path in paths if path not in chapters]
        self.assertEqual(len(chapters), 50)
        self.assertEqual(len(other), 12)
        self.assertNotIn("docs/chapter16/Chapter16-Graduation-Project.md", paths)


class RepositoryAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.outside_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.outside_root = Path(self.outside_dir.name)
        run_git(self.root, "init", "-q")
        run_git(self.root, "config", "user.email", "audit@example.invalid")
        run_git(self.root, "config", "user.name", "Audit Test")
        (self.root / "docs/chapter1").mkdir(parents=True)
        (self.root / "tools/independent_release").mkdir(parents=True)
        (self.root / "tools/independent_release/originality_allowlist.json").write_text(
            "[]\n", encoding="utf-8"
        )

        shared = "This baseline publication sentence contains enough words to trigger an exact prose finding.\n"
        (self.root / "docs/chapter1/en.md").write_text(shared, encoding="utf-8")
        (self.root / "docs/chapter1/image.png").write_bytes(b"same-image-bytes")
        run_git(self.root, "add", ".")
        run_git(self.root, "commit", "-qm", "baseline")
        run_git(self.root, "branch", "upstream/main")

    def tearDown(self):
        self.outside_dir.cleanup()
        self.temp_dir.cleanup()

    def test_repository_detects_identical_publication_blob_and_linked_image_sha256(self):
        markdown = self.root / "docs/chapter1/en.md"
        markdown.write_text(
            markdown.read_text(encoding="utf-8") + "\n![diagram](image.png)\n",
            encoding="utf-8",
        )
        findings = audit_repository(
            self.root,
            "upstream/main",
            [],
            includes=["docs/chapter1/**"],
        )
        kinds = {item.kind for item in findings}
        self.assertIn("image_sha256", kinds)
        self.assertIn("exact_sentence", kinds)

        markdown.write_text(
            "This baseline publication sentence contains enough words to trigger an exact prose finding.\n",
            encoding="utf-8",
        )
        findings = audit_repository(
            self.root,
            "upstream/main",
            [],
            includes=["docs/chapter1/en.md"],
        )
        self.assertIn("identical_publication_blob", {item.kind for item in findings})

    def test_repository_detects_duplicate_image_from_html_hero(self):
        markdown = self.root / "docs/chapter1/en.md"
        markdown.write_text(
            '<figure class="course-hero">\n'
            '  <IMG SRC="image.png" alt="Local hero">\n'
            '</figure>\n',
            encoding="utf-8",
        )

        findings = audit_repository(
            self.root,
            "upstream/main",
            [],
            includes=["docs/chapter1/en.md"],
        )

        image_findings = [item for item in findings if item.kind == "image_sha256"]
        self.assertEqual(len(image_findings), 1)
        self.assertEqual(image_findings[0].current_path, "docs/chapter1/image.png")

    def test_html_image_discovery_ignores_remote_data_and_path_escape_sources(self):
        escaped_image = self.outside_root / "escaped.png"
        escaped_image.write_bytes(b"same-image-bytes")
        escape_source = f"../../{self.outside_root.name}/escaped.png"
        markdown = self.root / "docs/chapter1/en.md"
        markdown.write_text(
            '<img src="image.png" alt="safe local image">\n'
            '<img src="https://example.invalid/not-fetched.png" alt="remote">\n'
            '<img src="data:image/png;base64,c2FtZS1pbWFnZS1ieXRlcw==" alt="data">\n'
            f'<img src="{escape_source}" alt="escape">\n',
            encoding="utf-8",
        )

        findings = audit_repository(
            self.root,
            "upstream/main",
            [],
            includes=["docs/chapter1/en.md"],
        )

        image_findings = [item for item in findings if item.kind == "image_sha256"]
        self.assertEqual(
            [item.current_path for item in image_findings],
            ["docs/chapter1/image.png"],
        )

    def test_repository_handles_missing_upstream_counterpart(self):
        new_path = self.root / "docs/chapter1/new.md"
        new_path.write_text("Entirely new publication prose.\n", encoding="utf-8")
        self.assertEqual(
            audit_repository(
                self.root,
                "upstream/main",
                [],
                includes=["docs/chapter1/new.md"],
            ),
            [],
        )

    def test_fnmatch_include_flags_are_repeatable_and_exact(self):
        (self.root / "docs/chapter2").mkdir(parents=True)
        (self.root / "docs/chapter2/en.md").write_text("new chapter two", encoding="utf-8")
        findings = audit_repository(
            self.root,
            "upstream/main",
            [],
            includes=["docs/chapter1/*.md", "docs/chapter2/*.md"],
        )
        audited_paths = {item.current_path for item in findings}
        self.assertIn("docs/chapter1/en.md", audited_paths)
        self.assertNotIn("docs/chapter1/image.png", audited_paths)

    def test_reports_are_deterministic_and_mark_unreviewed_files(self):
        finding = AuditFinding(
            kind="exact_sentence",
            current_path="docs/chapter1/en.md",
            upstream_path="docs/chapter1/en.md",
            excerpt="shared prose",
            location="line 3",
        )
        reviews = {"docs/chapter1/en.md": {
            "reviewed": False,
            "finding_count_before_review": 1,
            "rewritten_sections": [],
            "final_unallowed_count": 1,
            "review_notes": "",
        }}
        first = render_json_report([finding], reviews, "upstream/main", ["docs/chapter1/*.md"])
        second = render_json_report([finding], reviews, "upstream/main", ["docs/chapter1/*.md"])
        self.assertEqual(first, second)
        payload = json.loads(first)
        self.assertEqual(payload["summary"]["unallowed_findings"], 1)
        markdown = render_markdown_report([finding], reviews, "upstream/main", ["docs/chapter1/*.md"])
        self.assertIn("| docs/chapter1/en.md | no | 1 | 1 |", markdown)

    def test_cli_regeneration_preserves_reviewed_sections_in_json_and_markdown(self):
        report_dir = self.root / "docs/independent-release"
        report_dir.mkdir(parents=True)
        json_path = report_dir / "originality-report.json"
        markdown_path = report_dir / "originality-report.md"
        json_path.write_text(
            json.dumps({
                "reviews": {
                    "docs/chapter1/en.md": {
                        "reviewed": True,
                        "finding_count_before_review": 3,
                        "rewritten_sections": ["A rewritten explanation"],
                        "reviewed_sections": ["A manually reviewed example"],
                        "final_unallowed_count": 0,
                        "review_notes": "Bilingual review complete.",
                    }
                }
            }),
            encoding="utf-8",
        )

        result = subprocess.run(
            [
                "python3", str(SCRIPT),
                "--root", str(self.root),
                "--upstream", "upstream/main",
                "--include", "docs/chapter1/*.md",
                "--json", str(json_path),
                "--markdown", str(markdown_path),
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        regenerated = json.loads(json_path.read_text(encoding="utf-8"))
        review = regenerated["reviews"]["docs/chapter1/en.md"]
        self.assertEqual(review.get("reviewed_sections"), ["A manually reviewed example"])
        markdown = markdown_path.read_text(encoding="utf-8")
        self.assertIn(
            "| Current path | Reviewed | Before | Final | Rewritten sections | Reviewed sections | Review notes |",
            markdown,
        )
        self.assertIn(
            "| docs/chapter1/en.md | yes | 3 | 2 | A rewritten explanation | A manually reviewed example | Bilingual review complete. |",
            markdown,
        )

    def test_cli_writes_both_reports_and_exits_one_for_findings(self):
        json_path = self.root / "report.json"
        markdown_path = self.root / "report.md"
        result = subprocess.run(
            [
                "python3", str(SCRIPT),
                "--root", str(self.root),
                "--upstream", "upstream/main",
                "--include", "docs/chapter1/*.md",
                "--json", str(json_path),
                "--markdown", str(markdown_path),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertTrue(json_path.is_file())
        self.assertTrue(markdown_path.is_file())
        self.assertEqual(json.loads(json_path.read_text())["summary"]["unallowed_findings"], 2)


if __name__ == "__main__":
    unittest.main()
