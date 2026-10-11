"""Unit tests for content specification, creative brief, and profile validation."""

import unittest
from pathlib import Path

from src.renderer.validator import (
    ValidationError,
    load_profile,
    merge_creative_direction,
    validate_creative_brief,
    validate_spec,
)


class TestValidation(unittest.TestCase):

    def setUp(self):
        self.profiles_dir = Path("config/profiles")

    def test_load_existing_profiles(self):
        dev_prof = load_profile("developer_workflow", profiles_dir=self.profiles_dir)
        self.assertEqual(dev_prof.get("id"), "developer_workflow")
        self.assertIn("colors", dev_prof)
        self.assertIn("typography", dev_prof)
        self.assertIn("layout", dev_prof)

        edit_prof = load_profile("editorial_data_story", profiles_dir=self.profiles_dir)
        self.assertEqual(edit_prof.get("id"), "editorial_data_story")
        self.assertIn("colors", edit_prof)
        self.assertIn("typography", edit_prof)
        self.assertIn("layout", edit_prof)

    def test_load_nonexistent_profile_raises(self):
        with self.assertRaises(ValidationError) as ctx:
            load_profile("non_existent_profile", profiles_dir=self.profiles_dir)
        self.assertIn("not found", str(ctx.exception))

    def test_valid_spec_passes_with_portrait_defaults(self):
        valid_spec = {
            "title": "Test 9:16 Video",
            "profile": "developer_workflow",
            "output": {"width": 1080, "height": 1920, "fps": 30},
            "scenes": [
                {
                    "id": "s1",
                    "type": "title",
                    "duration": 3.0,
                    "headline": "Vertical Reel Title",
                }
            ],
        }
        errors = validate_spec(valid_spec)
        self.assertEqual(errors, [])

    def test_missing_required_fields(self):
        bad_spec = {"title": "Missing Scenes and Profile"}
        errors = validate_spec(bad_spec)
        self.assertTrue(any("profile" in err for err in errors))
        self.assertTrue(any("scenes" in err for err in errors))

    def test_invalid_scene_type(self):
        bad_scene_spec = {
            "title": "Bad Scene",
            "profile": "developer_workflow",
            "scenes": [
                {
                    "id": "s1",
                    "type": "unknown_scene_type",
                    "duration": 2.0,
                    "headline": "Test",
                }
            ],
        }
        errors = validate_spec(bad_scene_spec)
        self.assertTrue(any("unsupported type" in err for err in errors))

    def test_invalid_dimensions_and_duration(self):
        bad_spec = {
            "title": "Odd Dimensions",
            "profile": "developer_workflow",
            "output": {"width": 1081, "height": 1920, "fps": -5},
            "scenes": [
                {
                    "id": "s1",
                    "type": "title",
                    "duration": -2.0,
                    "headline": "Negative duration",
                }
            ],
        }
        errors = validate_spec(bad_spec)
        self.assertTrue(any("even integer" in err for err in errors))
        self.assertTrue(any("fps must be a positive" in err for err in errors))
        self.assertTrue(any("duration must be a positive" in err for err in errors))

    def test_creative_brief_validation_requires_approval(self):
        unapproved_brief = {
            "title": "Unapproved Brief",
            "base_profile": "developer_workflow",
            "visual_mood": "Moody dark",
            "pacing": "Fast",
            "transitions": "Cut",
            "rationale": "Testing approval gate",
            "approval": {"status": "pending_review"},
        }
        errors = validate_creative_brief(unapproved_brief, require_approval=True)
        self.assertTrue(any("Human approval is required" in err for err in errors))

        # When approval is waived (e.g. preview mode), it passes
        errors_no_req = validate_creative_brief(unapproved_brief, require_approval=False)
        self.assertEqual(errors_no_req, [])

    def test_creative_brief_direction_merging(self):
        base_prof = {
            "colors": {"background": "#000000", "accent": "#111111"},
            "typography": {"font_families": ["Arial"]},
        }
        brief = {
            "palette": {"accent": "#ff0000"},
            "typography": {"font_families": ["Georgia"]},
            "visual_mood": "Vibrant custom red",
            "approval": {"status": "approved"},
        }
        merged = merge_creative_direction(base_prof, brief)
        self.assertEqual(merged["colors"]["accent"], "#ff0000")
        self.assertEqual(merged["colors"]["background"], "#000000")
        self.assertEqual(merged["typography"]["font_families"], ["Georgia"])
        self.assertEqual(merged["_creative_brief"]["visual_mood"], "Vibrant custom red")


if __name__ == "__main__":
    unittest.main()
