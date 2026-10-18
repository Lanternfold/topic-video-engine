"""Tests for frame-based timeline scheduling and motion transforms."""

import unittest
from PIL import Image, ImageChops, ImageDraw

from src.renderer.timeline import (
    SUPPORTED_MOTION_PRESETS,
    apply_motion,
    build_timeline,
)


class TestTimeline(unittest.TestCase):
    def test_segments_are_contiguous_and_frame_counts_are_deterministic(self):
        timeline = build_timeline(
            [{"duration": 1.0}, {"duration": 1.5}, {"duration": 0.25}], 30
        )
        self.assertEqual([s.start_frame for s in timeline], [0, 30, 75])
        self.assertEqual([s.frame_count for s in timeline], [30, 45, 8])
        self.assertEqual([s.end_frame for s in timeline], [30, 75, 83])

    def test_invalid_fps_and_durations_are_rejected(self):
        with self.assertRaises(ValueError):
            build_timeline([{"duration": 1}], 0)
        with self.assertRaises(ValueError):
            build_timeline([{"duration": float("nan")}], 30)
        with self.assertRaises(ValueError):
            build_timeline([], 30)

    def test_static_motion_returns_same_pixels_in_a_new_image(self):
        image = Image.new("RGB", (80, 120), "black")
        result = apply_motion(image, "static", 0.5)
        self.assertEqual(result.size, image.size)
        self.assertIsNot(result, image)
        self.assertIsNone(ImageChops.difference(result, image).getbbox())

    def test_push_in_changes_pixels_over_time_and_preserves_frame_size(self):
        image = Image.new("RGB", (100, 100), "black")
        draw = ImageDraw.Draw(image)
        draw.rectangle((10, 10, 30, 30), fill="white")
        start = apply_motion(image, "push_in", 0.0, 0.2)
        end = apply_motion(image, "push_in", 1.0, 0.2)
        self.assertEqual(start.size, image.size)
        self.assertEqual(end.size, image.size)
        self.assertIsNotNone(ImageChops.difference(start, end).getbbox())

    def test_all_presets_return_target_dimensions(self):
        image = Image.new("RGB", (64, 96), "blue")
        for preset in SUPPORTED_MOTION_PRESETS:
            with self.subTest(preset=preset):
                result = apply_motion(image, preset, 0.5, 0.1)
                self.assertEqual(result.size, image.size)

    def test_unknown_preset_and_excessive_strength_are_rejected(self):
        image = Image.new("RGB", (64, 96), "blue")
        with self.assertRaises(ValueError):
            apply_motion(image, "spin", 0.5)
        with self.assertRaises(ValueError):
            apply_motion(image, "push_in", 0.5, 0.5)


if __name__ == "__main__":
    unittest.main()
