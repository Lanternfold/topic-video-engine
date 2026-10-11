"""End-to-end integration test for Topic Video Engine (9:16 vertical Reels & Shorts)."""

import tempfile
import unittest
from pathlib import Path

from src.renderer.render import render_video
from src.renderer.validator import ValidationError
from tests.validate_video import verify_video


class TestRenderEndToEnd(unittest.TestCase):

    def test_render_developer_workflow_vertical_e2e(self):
        spec_path = Path("prototypes/developer_workflow/sample.json")
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            out_path = render_video(spec_path=spec_path, output_path=tmp_path, verbose=False)
            self.assertTrue(out_path.is_file())

            # Expected total duration for developer sample is 3.0 + 3.5 + 3.5 + 3.0 = 13.0s
            info = verify_video(
                video_path=out_path,
                expected_width=1080,
                expected_height=1920,
                expected_fps=30.0,
                expected_duration=13.0,
                duration_tolerance=0.5,
            )
            self.assertEqual(info["width"], 1080)
            self.assertEqual(info["height"], 1920)
            self.assertEqual(info["codec"], "h264")
        finally:
            if tmp_path.is_file():
                tmp_path.unlink()

    def test_render_editorial_data_story_vertical_e2e(self):
        spec_path = Path("prototypes/editorial_data_story/sample.json")
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            out_path = render_video(spec_path=spec_path, output_path=tmp_path, verbose=False)
            self.assertTrue(out_path.is_file())

            # Expected total duration for editorial sample is 3.0 + 3.5 + 3.5 + 3.0 = 13.0s
            info = verify_video(
                video_path=out_path,
                expected_width=1080,
                expected_height=1920,
                expected_fps=30.0,
                expected_duration=13.0,
                duration_tolerance=0.5,
            )
            self.assertEqual(info["width"], 1080)
            self.assertEqual(info["height"], 1920)
            self.assertEqual(info["codec"], "h264")
        finally:
            if tmp_path.is_file():
                tmp_path.unlink()

    def test_render_rejects_unapproved_creative_brief(self):
        # Create temporary unapproved spec
        unapproved_spec = {
            "title": "Unapproved Test",
            "profile": "developer_workflow",
            "creative_brief": {
                "visual_mood": "Moody",
                "pacing": "Fast",
                "transitions": "Cut",
                "rationale": "Testing gate",
                "approval": {"status": "pending_review"}
            },
            "output": {"width": 1080, "height": 1920, "fps": 30},
            "scenes": [{"type": "title", "headline": "Draft", "duration": 1.0}]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            import json
            json.dump(unapproved_spec, f)
            spec_path = Path(f.name)

        try:
            with self.assertRaises(ValidationError) as ctx:
                render_video(spec_path=spec_path, require_approval=True, verbose=False)
            self.assertIn("Human approval is required", str(ctx.exception))
        finally:
            if spec_path.is_file():
                spec_path.unlink()


if __name__ == "__main__":
    unittest.main()
