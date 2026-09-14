from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urljoin, urlsplit


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
ZH_SIDEBAR = (DOCS / "_sidebar.md").read_text(encoding="utf-8")
EN_SIDEBAR = (DOCS / "_sidebar_en.md").read_text(encoding="utf-8")
INDEX_HTML = (DOCS / "index.html").read_text(encoding="utf-8")

EXPECTED_ZH_STAGES = [
    "第一阶段：Agentic AI 基础",
    "第二阶段：构建可运行 Agent",
    "第三阶段：上下文与外部能力",
    "第四阶段：优化、评测与安全",
    "第五阶段：期中项目",
    "第六阶段：模型原理与后训练",
    "第七阶段：推理与分布式基础设施",
    "第八阶段：Agentic UI 与生产系统",
    "第九阶段：毕业设计",
]

EXPECTED_EN_STAGES = [
    "Stage I: Agentic AI Foundations",
    "Stage II: Build a Working Agent",
    "Stage III: Context and External Capabilities",
    "Stage IV: Optimization, Evaluation, and Safety",
    "Stage V: Midterm Project",
    "Stage VI: Model Foundations and Post-Training",
    "Stage VII: Inference and Distributed Infrastructure",
    "Stage VIII: Agentic UI and Production Systems",
    "Stage IX: Graduation Project",
]

APPENDIX_PAIRS = {
    "附录A 自测题库.md": "Appendix-A-Question-Bank.md",
    "附录B 公式与系统速查.md": "Appendix-B-Formula-and-Systems-Cheat-Sheet.md",
    "附录C 实验与排错索引.md": "Appendix-C-Labs-and-Troubleshooting.md",
}


def markdown_links(markdown: str) -> list[str]:
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", markdown)


def chapter_links(markdown: str) -> list[str]:
    return [target for target in markdown_links(markdown) if "/chapter" in target or target.startswith("./chapter")]


def appendix_links(markdown: str) -> list[str]:
    return [target for target in markdown_links(markdown) if "/appendices/" in target or target.startswith("./appendices/")]


def resolve_docsify_target(target: str) -> Path | None:
    if re.match(r"^[a-z]+://", target):
        return None
    decoded = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if decoded.startswith("/en/"):
        decoded = decoded[len("/en/") :]
    elif decoded.startswith("/"):
        decoded = decoded[1:]
    elif decoded.startswith("./"):
        decoded = decoded[2:]
    return DOCS / decoded


def public_repository_targets(markdown: str) -> set[str]:
    prefix = "https://github.com/het2333/Go-Agentic/"
    targets = set()
    for target in markdown_links(markdown):
        if not target.startswith(prefix):
            continue
        match = re.match(rf"{re.escape(prefix)}(?:blob|tree)/main/([^?#]+)", target)
        if match:
            targets.add(unquote(match.group(1)))
    return targets


def mapping_has_chapter(chapter_number: int) -> bool:
    zh = re.search(rf"'第[^']*章[^']*\.md'\s*:\s*'Chapter{chapter_number}-[^']+\.md'", INDEX_HTML)
    en = re.search(rf"'Chapter{chapter_number}-[^']+\.md'\s*:\s*'第[^']*章[^']*\.md'", INDEX_HTML)
    return bool(zh and en)


def mapping_has_appendix(chinese_name: str, english_name: str) -> bool:
    zh = re.search(rf"'{re.escape(chinese_name)}'\s*:\s*'{re.escape(english_name)}'", INDEX_HTML)
    en = re.search(rf"'{re.escape(english_name)}'\s*:\s*'{re.escape(chinese_name)}'", INDEX_HTML)
    return bool(zh and en)


class CourseStructureTests(unittest.TestCase):
    def test_chapter_hero_urls_stay_inside_github_pages_project_path(self):
        publication_base = "https://example.test/Go-Agentic/"
        chapter_files = sorted(DOCS.glob("chapter*/*.md"))
        image_sources = []
        for chapter_file in chapter_files:
            markdown = chapter_file.read_text(encoding="utf-8")
            image_sources.extend(re.findall(r'<img[^>]+src="([^"]+)"', markdown))

        self.assertTrue(image_sources, "chapter pages must retain their visual assets")
        for source in image_sources:
            resolved = urlsplit(urljoin(publication_base, source)).path
            self.assertTrue(
                resolved.startswith("/Go-Agentic/assets/visuals/"),
                f"chapter hero escapes the GitHub Pages project path: {source} -> {resolved}",
            )

    def test_opening_case_links_to_runnable_lab_and_progressive_upgrade_map(self):
        homepage_expectations = (
            (DOCS / "README.md", "进入第一章查看完整轨迹", "./chapter1/第一章%20初识智能体.md"),
            (
                DOCS / "README_EN.md",
                "See the complete trace in Chapter 1",
                "./chapter1/Chapter1-Introduction-to-Agents.md",
            ),
        )
        for homepage_file, label, target in homepage_expectations:
            markdown = homepage_file.read_text(encoding="utf-8")
            self.assertIn(f"[{label}]({target})", markdown)
            self.assertNotIn("codex://", markdown)

        chapter_files = (
            (
                DOCS / "chapter1" / "第一章 初识智能体.md",
                "./appendices/附录C%20实验与排错索引.md",
            ),
            (
                DOCS / "chapter1" / "Chapter1-Introduction-to-Agents.md",
                "./appendices/Appendix-C-Labs-and-Troubleshooting.md",
            ),
        )
        expected_lab_targets = {
            "code/go-agentic/01-minimal-loop/CODING_AGENT.md",
            "code/go-agentic/01-minimal-loop/coding_agent_beginner.py",
            "code/go-agentic/01-minimal-loop/coding_agent.py",
        }
        for chapter_file, appendix_target in chapter_files:
            markdown = chapter_file.read_text(encoding="utf-8")
            targets = public_repository_targets(markdown)
            self.assertTrue(
                expected_lab_targets <= targets,
                f"opening case must expose the runnable guide and implementation: {chapter_file}",
            )
            self.assertNotIn("codex://", markdown)
            self.assertIn(appendix_target, markdown_links(markdown))

        appendix_files = (
            DOCS / "appendices" / "附录C 实验与排错索引.md",
            DOCS / "appendices" / "Appendix-C-Labs-and-Troubleshooting.md",
        )
        for appendix_file in appendix_files:
            markdown = appendix_file.read_text(encoding="utf-8")
            targets = public_repository_targets(markdown)
            self.assertIn("code/go-agentic/01-minimal-loop/CODING_AGENT.md", targets)
            self.assertNotIn("codex://", markdown)
            linked_chapters = {
                int(match.group(1))
                for target in chapter_links(markdown)
                if (match := re.search(r"chapter(\d+)", target, re.IGNORECASE))
            }
            self.assertTrue(
                {4, 5, 9, 12, 24} <= linked_chapters,
                f"progressive lab map is incomplete: {appendix_file}",
            )

        for target in expected_lab_targets:
            self.assertTrue((ROOT / target).is_file(), f"missing opening-case lab target: {target}")

    def test_cdn_dependencies_are_exactly_pinned_to_browser_verified_versions(self):
        expected_urls = (
            "//cdn.jsdelivr.net/npm/docsify@4.13.1/lib/themes/vue.css",
            "//cdn.jsdelivr.net/npm/mermaid@11.12.1/dist/mermaid.min.js",
            "//cdn.jsdelivr.net/npm/docsify@5.0.0/lib/docsify.min.js",
            "//cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-bash.js",
            "//cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-python.js",
            "//cdn.jsdelivr.net/npm/docsify-pagination@2.10.1/dist/docsify-pagination.min.js",
            "//cdn.jsdelivr.net/npm/docsify-copy-code@3.0.2/dist/docsify-copy-code.min.js",
            "//cdn.jsdelivr.net/npm/docsify@5.0.0/lib/plugins/zoom-image.min.js",
            "https://cdn.jsdelivr.net/npm/katex@0.18.7/dist/katex.min.js",
            "//cdn.jsdelivr.net/npm/katex@0.18.7/dist/katex.min.css",
            "https://cdn.jsdelivr.net/npm/marked@3.0.8/marked.min.js",
            "//cdn.jsdelivr.net/npm/docsify-katex@2.0.2/dist/docsify-katex.js",
            "//unpkg.com/docsify-count@1.1.0/dist/countable.js",
        )
        for url in expected_urls:
            self.assertIn(url, INDEX_HTML, f"missing browser-verified CDN pin: {url}")
        self.assertNotIn("@latest", INDEX_HTML)

    def test_sidebars_have_25_chapters_and_nine_stages(self):
        self.assertTrue(all(stage in ZH_SIDEBAR for stage in EXPECTED_ZH_STAGES))
        self.assertTrue(all(stage in EN_SIDEBAR for stage in EXPECTED_EN_STAGES))
        self.assertEqual(len(chapter_links(ZH_SIDEBAR)), 25)
        self.assertEqual(len(chapter_links(EN_SIDEBAR)), 25)

    def test_every_sidebar_markdown_target_exists(self):
        for target in markdown_links(ZH_SIDEBAR) + markdown_links(EN_SIDEBAR):
            resolved = resolve_docsify_target(target)
            if resolved is not None:
                self.assertTrue(resolved.is_file(), f"missing sidebar target: {target} -> {resolved}")

    def test_language_mapping_contains_every_chapter(self):
        for chapter_number in range(1, 26):
            self.assertTrue(mapping_has_chapter(chapter_number), f"missing bilingual mapping for chapter {chapter_number}")

    def test_sidebars_and_language_mapping_contain_three_appendices(self):
        self.assertEqual(len(appendix_links(ZH_SIDEBAR)), 3)
        self.assertEqual(len(appendix_links(EN_SIDEBAR)), 3)
        for chinese_name, english_name in APPENDIX_PAIRS.items():
            self.assertTrue(
                mapping_has_appendix(chinese_name, english_name),
                f"missing bilingual mapping for appendix: {chinese_name}",
            )

    def test_learning_path_switch_has_three_bilingual_persisted_filtered_routes(self):
        self.assertIn("switcher.id = 'learningPathSwitch'", INDEX_HTML)
        self.assertIn('class="learning-path-indicator"', INDEX_HTML)
        self.assertIn("learning-path-preference", INDEX_HTML)
        self.assertIn('src="./assets/learning-path.js"', INDEX_HTML)
        self.assertIn("filterSidebar(activePath)", INDEX_HTML)
        self.assertIn("filterHomepage(activePath)", INDEX_HTML)
        self.assertIn("updatePagination(activePath)", INDEX_HTML)
        self.assertIn('aria-pressed="true"', INDEX_HTML)
        self.assertIn("classList.add('learning-path-pending')", INDEX_HTML)
        self.assertIn("classList.remove('learning-path-pending')", INDEX_HTML)
        for route_id in ("application", "fullstack", "systems"):
            self.assertIn(f'data-path="{route_id}"', INDEX_HTML)

        chinese_home = (DOCS / "README.md").read_text(encoding="utf-8")
        english_home = (DOCS / "README_EN.md").read_text(encoding="utf-8")
        for route_id in ("application", "fullstack", "systems"):
            self.assertIn(f'id="route-{route_id}"', chinese_home)
            self.assertIn(f'id="route-{route_id}"', english_home)

    def test_site_uses_deep_ocean_blue_palette_and_responsive_switch_position(self):
        palette = INDEX_HTML.lower()
        for token in (
            "--brand-blue: #2563eb",
            "--brand-cyan: #06b6d4",
            "--brand-amber: #f59e0b",
            "--light-bg: #f7f9fc",
            "--dark-bg: #0b1220",
        ):
            self.assertIn(token, palette)

        desktop_switch = re.search(r"\.learning-path-switch\s*\{(?P<body>.*?)\}", palette, re.DOTALL)
        self.assertIsNotNone(desktop_switch)
        self.assertIn("margin: 0 0 28px auto", desktop_switch.group("body"))
        self.assertIn("top: -20px", desktop_switch.group("body"))

        mobile = re.search(r"@media screen and \(max-width: 768px\)\s*\{(?P<body>.*)\}\s*</style>", palette, re.DOTALL)
        self.assertIsNotNone(mobile)
        mobile_switch = re.search(r"\.learning-path-switch\s*\{(?P<body>.*?)\}", mobile.group("body"), re.DOTALL)
        self.assertIsNotNone(mobile_switch)
        self.assertIn("margin: 0 0 22px auto", mobile_switch.group("body"))
        self.assertIn("top: 0", mobile_switch.group("body"))

        mobile_language_switch = re.search(r"\.lang-switch\s*\{(?P<body>.*?)\}", mobile.group("body"), re.DOTALL)
        self.assertIsNotNone(mobile_language_switch)
        self.assertIn("top: 10px", mobile_language_switch.group("body"))
        self.assertRegex(
            palette,
            r"body\.dark-mode \.learning-route-badge\s*\{[^}]*color:\s*#fbbf24",
        )

    def test_docsify_renders_responsive_heroes_and_mermaid_in_both_themes(self):
        palette = INDEX_HTML.lower()
        hero_figure = re.search(
            r"\.markdown-section figure\.course-hero\s*\{(?P<body>.*?)\}",
            palette,
            re.DOTALL,
        )
        self.assertIsNotNone(hero_figure)
        self.assertIn("max-width: 100%", hero_figure.group("body"))

        hero_image = re.search(
            r"\.markdown-section figure\.course-hero img\s*\{(?P<body>.*?)\}",
            palette,
            re.DOTALL,
        )
        self.assertIsNotNone(hero_image)
        for declaration in ("border-radius: 16px", "display: block", "height: auto", "width: 100%"):
            self.assertIn(declaration, hero_image.group("body"))
        self.assertIn("aspect-ratio: 16 / 9", hero_image.group("body"))

        self.assertRegex(
            palette,
            r"body\.dark-mode \.markdown-section figure\.course-hero img\s*\{[^}]*border-color:\s*var\(--dark-border\)",
        )
        self.assertIn("body.dark-mode .markdown-section .mermaid", palette)
        self.assertNotIn("filter: invert(1) hue-rotate(180deg)", palette)
        self.assertIn(".markdown-section .mermaid svg", palette)
        self.assertIn("max-width: 100%", palette)
        for token in (
            "theme: 'base'",
            "primarycolor: '#0b1220'",
            "primarybordercolor: '#2563eb'",
            "linecolor: '#2563eb'",
            "secondarycolor: '#0f172a'",
            "tertiarycolor: '#111827'",
        ):
            self.assertIn(token, palette)
        self.assertRegex(palette, r"\.markdown-section \.mermaid\s*\{[^}]*background:\s*var\(--light-surface\)")
        self.assertRegex(
            palette,
            r"body\.dark-mode \.markdown-section \.mermaid\s*\{[^}]*background:\s*var\(--dark-bg\)",
        )
        for legend_class in ("data", "control", "failure", "approval"):
            self.assertIn(f".diagram-legend-{legend_class}::before", palette)
        self.assertIn("mermaid.run({ nodes: diagrams })", INDEX_HTML)
        self.assertLess(INDEX_HTML.index("mermaid.run({ nodes: diagrams })"), INDEX_HTML.index("applyLearningPathView();"))

        mobile = re.search(r"@media screen and \(max-width: 768px\)\s*\{(?P<body>.*)\}\s*</style>", palette, re.DOTALL)
        self.assertIsNotNone(mobile)
        mobile_diagram = re.search(r"\.markdown-section \.mermaid\s*\{(?P<body>.*?)\}", mobile.group("body"), re.DOTALL)
        self.assertIsNotNone(mobile_diagram)
        self.assertIn("max-width: 100%", mobile_diagram.group("body"))
        self.assertIn("overflow-x: auto", mobile_diagram.group("body"))
        mobile_svg = re.search(r"\.markdown-section \.mermaid svg\s*\{(?P<body>.*?)\}", mobile.group("body"), re.DOTALL)
        self.assertIsNotNone(mobile_svg)
        self.assertIn("max-width: none", mobile_svg.group("body"))
        self.assertIn("min-width: 680px", mobile_svg.group("body"))


if __name__ == "__main__":
    unittest.main()
