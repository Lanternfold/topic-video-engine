"""Unit tests for scene rendering across both visual profiles in 9:16 vertical format."""

import unittest
from pathlib import Path
from PIL import Image

from src.renderer.validator import load_profile
from src.scenes.registry import get_scene_renderer


class TestSceneRendering(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.profiles = {
            "developer_workflow": load_profile("developer_workflow", Path("config/profiles")),
            "editorial_data_story": load_profile("editorial_data_story", Path("config/profiles")),
        }

    def _test_scene(self, scene_type: str, scene_data: dict):
        for profile_id, profile in self.profiles.items():
            renderer = get_scene_renderer(scene_type, profile=profile, width=1080, height=1920)
            img = renderer.render(scene_data)
            self.assertIsInstance(img, Image.Image, f"Failed for {scene_type} in {profile_id}")
            self.assertEqual(img.size, (1080, 1920), f"Size mismatch for {scene_type} in {profile_id}")
            self.assertEqual(img.mode, "RGB")

    def test_title_scene(self):
        self._test_scene(
            "title",
            {
                "headline": "Vertical Reel Title",
                "supporting_text": "A detailed explanation for testing title scenes in 9:16 vertical format",
                "tag": "COVER // 9:16 REEL",
                "footnote": "Footnote attribution test",
            },
        )

    def test_terminal_scene(self):
        self._test_scene(
            "terminal_workflow",
            {
                "headline": "Terminal Workflow Step",
                "supporting_text": "Running automated regression suite",
                "terminal": {
                    "command": "pytest --version",
                    "output": ["pytest 8.0.0", "✓ all checks passed"],
                },
                "footnote": "Captured from CI runner",
            },
        )

    def test_chart_scene(self):
        self._test_scene(
            "data_chart",
            {
                "headline": "Data Metrics Benchmark",
                "supporting_text": "Comparative analysis across configurations",
                "data_points": [
                    {"label": "Alpha", "value": 100, "unit": "ms"},
                    {"label": "Beta", "value": 50, "unit": "ms"},
                    {"label": "Gamma", "value": 25, "unit": "ms"},
                ],
                "footnote": "Source: Benchmark test suite",
            },
        )

    def test_stat_scene(self):
        self._test_scene(
            "stat_callout",
            {
                "headline": "Major Metric Highlight",
                "stat_value": "$100M",
                "stat_label": "Total Infrastructure Investment",
                "supporting_text": "Over 50% year-on-year growth observed",
                "footnote": "Annual Financial Report",
            },
        )

    def test_conclusion_scene(self):
        self._test_scene(
            "conclusion",
            {
                "headline": "Final Summary Takeaways",
                "supporting_text": "Critical points to implement",
                "bullet_points": [
                    "First recommendation for the team",
                    "Second architectural takeaway",
                    "Third long-term strategy",
                ],
            },
        )


if __name__ == "__main__":
    unittest.main()
