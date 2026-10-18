"""Tests for timed burned-in captions."""

import unittest
from PIL import Image

from src.renderer.captions import active_caption, draw_caption
from src.renderer.validator import validate_spec


class TestTimedCaptions(unittest.TestCase):
    def test_caption_uses_half_open_time_intervals(self):
        track = [
            {"start": 0.0, "end": 1.0, "text": "First"},
            {"start": 1.0, "end": 2.0, "text": "Second"},
        ]
        self.assertEqual(active_caption(track, 0.0), "First")
        self.assertIsNone(active_caption(track, 1.0 - 1e-6))
        self.assertEqual(active_caption(track, 1.0), "Second")
        self.assertIsNone(active_caption(track, 2.0))

    def test_caption_rendering_preserves_frame_dimensions(self):
        image = Image.new("RGB", (360, 640), "navy")
        rendered = draw_caption(image, "A timed caption that wraps onto multiple lines", 80, 24)
        self.assertEqual(rendered.size, image.size)
        self.assertEqual(rendered.mode, "RGB")

    def test_blank_caption_does_not_change_pixels(self):
        image = Image.new("RGB", (100, 150), "black")
        rendered = draw_caption(image, "   ")
        self.assertEqual(list(image.getdata()), list(rendered.getdata()))

    def test_invalid_caption_times_are_rejected_by_spec_validation(self):
        spec = {
            "title": "Caption test",
            "profile": "developer_workflow",
            "creative_brief": {
                "visual_mood": "Test",
                "pacing": "Measured",
                "transitions": "Cuts",
                "rationale": "Test",
                "approval": {"status": "approved"},
            },
            "scenes": [{
                "type": "title", "duration": 2.0, "headline": "Test",
                "captions": [{"start": 1.5, "end": 2.5, "text": "Too late"}],
            }],
        }
        errors = validate_spec(spec)
        self.assertTrue(any("no later than scene duration" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
