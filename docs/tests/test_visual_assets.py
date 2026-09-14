import hashlib
import json
from pathlib import Path
import unittest

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
VISUALS = ROOT / "docs" / "assets" / "visuals"
MANIFEST = VISUALS / "manifest.json"
EXPECTED_HERO_IDS = ["home"] + [f"chapter-{number:02d}" for number in range(1, 26)]
EXPECTED_SECTION_IDS = ["chapter-01-coding-loop"]
EXPECTED_INFOGRAPHIC_IDS = [
    "chapter-01-coding-workflow-zh",
    "chapter-01-coding-workflow-en",
]
EXPECTED_IDS = (
    EXPECTED_HERO_IDS[:2]
    + EXPECTED_SECTION_IDS
    + EXPECTED_INFOGRAPHIC_IDS
    + EXPECTED_HERO_IDS[2:]
)
REQUIRED_PROMPT_PHRASES = (
    "scientific-educational",
    "text-free editorial technical illustration",
    "deep-ocean blue #2563EB",
    "electric cyan #06B6D4",
    "restrained amber #F59E0B",
    "no letters",
    "no numerals",
    "no formulas",
    "no logos",
    "no brands",
    "no watermarks",
    "no third-party characters",
    "no screenshots",
    "original composition",
)


class VisualAssetTests(unittest.TestCase):
    def test_amber_is_restrained_to_compact_cue_regions(self):
        for asset_id in ("home", "chapter-22"):
            with self.subTest(asset=asset_id):
                path = VISUALS / f"{asset_id}.webp"
                with Image.open(path) as image:
                    rgb = image.convert("RGB")
                    warm_pixels = [
                        (x, y)
                        for y in range(rgb.height)
                        for x in range(rgb.width)
                        if (
                            (pixel := rgb.getpixel((x, y)))[0] >= 120
                            and pixel[0] >= pixel[2] * 1.35
                            and pixel[1] >= pixel[2] * 0.65
                            and pixel[1] <= pixel[0] * 0.9
                        )
                    ]

                self.assertTrue(warm_pixels)
                canvas_area = rgb.width * rgb.height
                warm_fraction = len(warm_pixels) / canvas_area
                self.assertLessEqual(warm_fraction, 0.002)

                xs = [point[0] for point in warm_pixels]
                ys = [point[1] for point in warm_pixels]
                cue_area = (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1)
                self.assertLessEqual(cue_area / canvas_area, 0.006)

    def test_reviewed_prompts_preserve_specific_visual_contracts(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        prompts = {item["id"]: item["prompt"] for item in manifest}

        home_prompt = prompts["home"]
        self.assertIn(
            "exactly one compact guarded approval connection only",
            home_prompt,
        )
        self.assertIn(
            "explicitly forbid amber, gold, orange, or yellow anywhere else",
            home_prompt.lower(),
        )

        chapter_22_prompt = prompts["chapter-22"]
        for phrase in (
            "distributed-training and RLHF infrastructure",
            "multiple distinct processor/GPU towers or compute nodes",
            "synchronized cyan model-shard and gradient circulation",
            "one dominant coordinated training core",
            "exactly one compact amber RLHF feedback/approval injection gate",
        ):
            self.assertIn(phrase, chapter_22_prompt)
        self.assertNotIn("continuous agent improvement", chapter_22_prompt)

    def test_required_heroes_are_fully_opaque(self):
        for asset_id in ("chapter-14", "chapter-25"):
            with self.subTest(asset=asset_id):
                path = VISUALS / f"{asset_id}.webp"
                with Image.open(path) as image:
                    alpha = image.convert("RGBA").getchannel("A")
                    self.assertEqual(alpha.getextrema(), (255, 255))

    def test_visual_directory_contains_only_release_assets(self):
        expected_files = {"manifest.json"} | {
            f"{asset_id}.webp" for asset_id in EXPECTED_IDS
        }
        actual_files = {
            path.relative_to(VISUALS).as_posix()
            for path in VISUALS.rglob("*")
            if path.is_file()
        }
        self.assertEqual(
            actual_files,
            expected_files,
            "docs/assets/visuals must recursively contain only manifest-backed release assets",
        )

    def test_visual_manifest_and_files(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual([item["id"] for item in manifest], EXPECTED_IDS)
        prompts = [item["prompt"] for item in manifest]
        hashes = [item["sha256"] for item in manifest]
        self.assertEqual(len(set(prompts)), len(EXPECTED_IDS), "all generation prompts must be pairwise unique")
        self.assertEqual(len(set(hashes)), len(EXPECTED_IDS), "all visual SHA-256 values must be pairwise unique")

        for item in manifest:
            with self.subTest(asset=item["id"]):
                self.assertEqual(item["generation_mode"], "built-in image_gen")
                is_infographic = item["id"] in EXPECTED_INFOGRAPHIC_IDS
                self.assertIs(item["contains_text"], is_infographic)
                if item["id"] in EXPECTED_SECTION_IDS:
                    expected_role = "section-illustration"
                elif is_infographic:
                    expected_role = "section-infographic"
                else:
                    expected_role = "hero"
                self.assertEqual(item.get("role", "hero"), expected_role)
                if is_infographic:
                    expected_language = "zh" if item["id"].endswith("-zh") else "en"
                    self.assertEqual(item.get("language"), expected_language)
                    self.assertEqual(item.get("ingestion_mode"), "user-supplied attachment")
                    self.assertEqual(item.get("source_format"), "PNG converted to WebP")
                self.assertEqual(set(item["alt_text"]), {"en", "zh"})
                self.assertEqual(set(item["caption"]), {"en", "zh"})
                for metadata in (item["alt_text"], item["caption"]):
                    self.assertTrue(metadata["en"].strip())
                    self.assertTrue(metadata["zh"].strip())
                required_phrases = (
                    ("scientific-educational", "no logos", "no watermarks")
                    if is_infographic
                    else REQUIRED_PROMPT_PHRASES
                )
                for phrase in required_phrases:
                    self.assertIn(phrase, item["prompt"])

                path = VISUALS / f'{item["id"]}.webp'
                self.assertTrue(path.is_file(), path.relative_to(ROOT))
                data = path.read_bytes()
                self.assertLessEqual(len(data), 500 * 1024)
                self.assertEqual(item["size_bytes"], len(data))
                self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"])

                with Image.open(path) as image:
                    self.assertEqual(image.format, "WEBP")
                    expected_size = (1672, 941) if is_infographic else (1536, 864)
                    self.assertEqual(image.size, expected_size)
                    self.assertEqual(item["width"], image.width)
                    self.assertEqual(item["height"], image.height)


if __name__ == "__main__":
    unittest.main()
