import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
MANIFEST = {
    entry["id"]: entry
    for entry in json.loads((DOCS / "assets" / "visuals" / "manifest.json").read_text(encoding="utf-8"))
}
INHERITED_CHAPTER_16_REDIRECTS = {
    "Chapter16-Graduation-Project.md",
    "第十六章 毕业设计.md",
}
DIAGRAM_CHAPTERS = {4, 5, 8, 9, 10, 11, 12, 17, 20, 21, 22, 23, 24}
DIAGRAM_SEMANTICS = {
    4: {"data", "control", "failure"},
    5: {"data", "control", "failure", "approval"},
    8: {"data", "control", "failure"},
    9: {"data", "control", "failure"},
    10: {"data", "control"},
    11: {"data", "control", "failure"},
    12: {"data", "control", "failure", "approval"},
    17: {"data", "control"},
    20: {"data"},
    21: {"data", "control"},
    22: {"data", "control"},
    23: {"data", "control", "failure", "approval"},
    24: {"data", "control", "failure", "approval"},
}
SEMANTIC_STROKES = {
    "data": ("#0E7490", "2", "0"),
    "control": ("#2563EB", "2", "6 3"),
    "failure": ("#64748B", "2", "2 3"),
    "approval": ("#B45309", "3", "10 4"),
}


def chapter_markdown_files(chapter: int) -> list[Path]:
    files = [
        path
        for path in sorted((DOCS / f"chapter{chapter}").glob("*.md"))
        if path.name not in INHERITED_CHAPTER_16_REDIRECTS
    ]
    if len(files) != 2:
        raise AssertionError(f"chapter {chapter} must have one active Chinese/English pair: {files}")
    return files


def publication_markdown_files() -> list[Path]:
    files = [DOCS / "README.md", DOCS / "README_EN.md"]
    for chapter in range(1, 26):
        files.extend(chapter_markdown_files(chapter))
    return files


def is_english(file: Path) -> bool:
    return file.name == "README_EN.md" or file.name.startswith("Chapter")


def hero_contract(file: Path, asset_id: str, source: str) -> str:
    language = "en" if is_english(file) else "zh"
    metadata = MANIFEST[asset_id]
    return (
        '<figure class="course-hero">\n'
        f'  <img src="{source}" alt="{metadata["alt_text"][language]}" '
        'width="1536" height="864" loading="lazy" decoding="async">\n'
        f'  <figcaption><em>{metadata["caption"][language]}</em></figcaption>\n'
        "</figure>"
    )


def diagram_body(file: Path) -> str:
    match = re.search(r"```mermaid\n(?P<body>.*?)\n```", file.read_text(encoding="utf-8"), re.DOTALL)
    if match is None:
        raise AssertionError(f"missing Mermaid diagram: {file}")
    return match.group("body")


def contrast_ratio(foreground: str, background: str) -> float:
    def luminance(color: str) -> float:
        channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    lighter, darker = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def edge_semantics(body: str) -> list[str | None]:
    edge_count = body.count("-->")
    semantics: list[str | None] = [None] * edge_count
    contract_to_semantic = {contract: semantic for semantic, contract in SEMANTIC_STROKES.items()}
    link_styles = re.finditer(
        r"(?m)^\s*linkStyle\s+(?P<targets>default|[\d,]+)\s+"
        r"stroke:(?P<stroke>#[0-9A-F]{6}),stroke-width:(?P<width>\d+)px,"
        r"stroke-dasharray:(?P<dash>[\d ]+)\s*$",
        body,
    )
    for style in link_styles:
        contract = (style.group("stroke"), style.group("width"), style.group("dash"))
        semantic = contract_to_semantic.get(contract)
        if semantic is None:
            continue
        targets = range(edge_count) if style.group("targets") == "default" else (
            int(index) for index in style.group("targets").split(",")
        )
        for target in targets:
            if target < edge_count:
                semantics[target] = semantic
    return semantics


class VisualReferenceTests(unittest.TestCase):
    def test_every_required_diagram_declares_localized_accessibility_metadata(self):
        for chapter in DIAGRAM_CHAPTERS:
            for file in chapter_markdown_files(chapter):
                body = diagram_body(file)
                titles = re.findall(r"(?m)^\s*accTitle:\s*(\S.*)$", body)
                descriptions = re.findall(r"(?m)^\s*accDescr:\s*(\S.*)$", body)
                self.assertEqual(len(titles), 1, f"one accTitle required in {file}")
                self.assertEqual(len(descriptions), 1, f"one accDescr required in {file}")
                self.assertGreaterEqual(len(titles[0]), 6, f"specific accTitle required in {file}")
                self.assertGreaterEqual(len(descriptions[0]), 20, f"specific accDescr required in {file}")
                if is_english(file):
                    self.assertNotRegex(titles[0] + descriptions[0], r"[\u3400-\u9fff]", str(file))
                else:
                    self.assertRegex(titles[0], r"[\u3400-\u9fff]", str(file))
                    self.assertRegex(descriptions[0], r"[\u3400-\u9fff]", str(file))

    def test_every_chapter_pair_references_its_hero(self):
        for chapter in range(1, 26):
            expected = f"../assets/visuals/chapter-{chapter:02d}.webp"
            for file in chapter_markdown_files(chapter):
                self.assertIn(
                    expected,
                    file.read_text(encoding="utf-8"),
                    f"missing chapter {chapter} hero reference in {file}",
                )

    def test_no_legacy_image_references(self):
        for file in publication_markdown_files():
            self.assertNotIn(
                "../images/",
                file.read_text(encoding="utf-8"),
                f"legacy image reference remains in {file}",
            )

    def test_manifest_metadata_builds_the_semantic_hero_immediately_after_each_h1(self):
        cases = [
            (DOCS / "README.md", "home", "./assets/visuals/home.webp"),
            (DOCS / "README_EN.md", "home", "./assets/visuals/home.webp"),
        ]
        for chapter in range(1, 26):
            cases.extend(
                (file, f"chapter-{chapter:02d}", f"../assets/visuals/chapter-{chapter:02d}.webp")
                for file in chapter_markdown_files(chapter)
            )

        for file, asset_id, source in cases:
            text = file.read_text(encoding="utf-8")
            expected = hero_contract(file, asset_id, source)
            self.assertEqual(text.count(source), 1, f"hero reference count in {file}")
            self.assertRegex(
                text,
                rf"(?m)^# [^\n]+\n\n{re.escape(expected)}",
                f"manifest-backed semantic hero must immediately follow H1 in {file}",
            )

    def test_only_required_chapters_have_one_language_matched_mermaid_diagram(self):
        for chapter in range(1, 26):
            for file in chapter_markdown_files(chapter):
                text = file.read_text(encoding="utf-8")
                expected_count = 1 if chapter in DIAGRAM_CHAPTERS else 0
                self.assertEqual(text.count("```mermaid"), expected_count, str(file))
                if expected_count:
                    diagram = re.search(r"```mermaid\n(?P<body>.*?)\n```", text, re.DOTALL)
                    self.assertIsNotNone(diagram, str(file))
                    body = diagram.group("body")
                    if is_english(file):
                        self.assertNotRegex(body, r"[\u3400-\u9fff]", str(file))
                        self.assertEqual(text.count("*Diagram conclusion:*"), 1, str(file))
                    else:
                        self.assertRegex(body, r"[\u3400-\u9fff]", str(file))
                        self.assertEqual(text.count("*图示结论：*"), 1, str(file))

    def test_each_diagram_uses_each_declared_semantic_edge_and_relevant_legend(self):
        class_contracts = {
            "data": "classDef data fill:#0B1220,stroke:#0E7490",
            "control": "classDef control fill:#0F172A,stroke:#2563EB",
            "failure": "classDef failure fill:#111827,stroke:#64748B",
            "approval": "classDef approval fill:#0B1220,stroke:#B45309",
        }
        legend_contracts = {
            "en": {
                "data": "Data · solid cyan",
                "control": "Control · dashed blue",
                "failure": "Failure · dotted neutral",
                "approval": "Approval/risk · long-dashed amber",
            },
            "zh": {
                "data": "数据 · 青色实线",
                "control": "控制 · 蓝色虚线",
                "failure": "失败 · 中性色点线",
                "approval": "审批/风险 · 琥珀色长虚线",
            },
        }
        for chapter in DIAGRAM_CHAPTERS:
            for file in chapter_markdown_files(chapter):
                text = file.read_text(encoding="utf-8")
                body = diagram_body(file)
                present = DIAGRAM_SEMANTICS[chapter]
                language = "en" if is_english(file) else "zh"
                for semantic, contract in class_contracts.items():
                    if semantic in present:
                        self.assertIn(contract, body, str(file))
                        self.assertIn(legend_contracts[language][semantic], text, str(file))
                    else:
                        self.assertNotIn(f"classDef {semantic} ", body, str(file))
                        self.assertNotIn(legend_contracts[language][semantic], text, str(file))
                effective_semantics = edge_semantics(body)
                self.assertNotIn(None, effective_semantics, f"every edge needs a semantic style in {file}")
                self.assertEqual(set(effective_semantics), present, str(file))
                if is_english(file):
                    self.assertIn('aria-label="Flow legend"', text, str(file))
                else:
                    self.assertIn('aria-label="流程图例"', text, str(file))

    def test_mermaid_stroke_variants_have_graphical_contrast_in_both_themes(self):
        index = (DOCS / "index.html").read_text(encoding="utf-8")
        for brand_token in (
            "--brand-blue: #2563EB",
            "--brand-cyan: #06B6D4",
            "--brand-amber: #F59E0B",
        ):
            self.assertIn(brand_token, index)

        for semantic, (stroke, _, _) in SEMANTIC_STROKES.items():
            self.assertIn(f"--diagram-{semantic}-stroke: {stroke}", index)
            for ground in ("#FFFFFF", "#F7F9FC", "#0B1220"):
                self.assertGreaterEqual(
                    contrast_ratio(stroke, ground),
                    3.0,
                    f"{semantic} stroke {stroke} against {ground}",
                )

    def test_wide_diagrams_use_stacked_topology(self):
        for chapter in (12, 17, 21):
            for file in chapter_markdown_files(chapter):
                self.assertTrue(diagram_body(file).startswith("flowchart TB"), str(file))

    def test_context_budget_gates_model_and_reassembles_after_compaction(self):
        for file in chapter_markdown_files(9):
            body = diagram_body(file)
            self.assertIn('Assemble --> ContextBudget{"', body)
            self.assertRegex(body, r"ContextBudget -- (Within budget|预算内) --> Model")
            self.assertRegex(body, r"ContextBudget -- (Over budget|超出预算) --> Compact")
            self.assertIn("Compact --> Preserve", body)
            self.assertIn("Preserve --> Assemble", body)
            self.assertNotIn("Assemble --> Model", body)

    def test_reasoning_selection_follows_pruning_and_ranking(self):
        for file in chapter_markdown_files(11):
            body = diagram_body(file)
            self.assertIn("Judge --> Prune", body)
            self.assertIn("Prune --> Rank", body)
            self.assertIn("Rank --> Select", body)
            self.assertIn('Select --> Done{"', body)
            self.assertNotIn("Judge --> Select", body)

    def test_recovery_scanner_reads_durable_state_before_requeue_decision(self):
        for file in chapter_markdown_files(24):
            body = diagram_body(file)
            self.assertIn("Store --> Recovery", body)
            self.assertIn("Recovery --> Recoverable", body)
            self.assertRegex(body, r"Recoverable -- (Yes|是) --> Queue")
            self.assertRegex(body, r"Recoverable -- (No|否) --> Failed")
            self.assertNotIn("Recovery --> Store", body)


if __name__ == "__main__":
    unittest.main()
