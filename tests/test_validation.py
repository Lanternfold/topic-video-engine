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

    def test_creative_brief_upgrade_fields(self):
        valid_upgraded_brief = {
            "title": "Kinetic Brief",
            "base_profile": "kinetic_editorial",
            "visual_mood": "High energy investigative",
            "pacing": "Fast",
            "transitions": "Editorial wipe",
            "rationale": "High contrast mobile engagement",
            "art_direction": {
                "treatment": "kinetic_editorial",
                "rationale": "High velocity typography"
            },
            "motion_intensity": "kinetic",
            "personal_signature": {
                "type": "dry_aside",
                "moment": "Closing takeaway note",
                "rationale": "Understated observation"
            },
            "mobile_safe_area": {"top": 140, "bottom": 180, "sides": 72},
            "evidence": [
                {
                    "source_url": "https://example.com/data",
                    "retrieved_at": "2026-10-18T12:00:00Z",
                    "note": "Audited benchmark figures",
                    "verification_status": "verified"
                }
            ],
            "approval": {"status": "approved"}
        }
        errors = validate_creative_brief(valid_upgraded_brief)
        self.assertEqual(errors, [])

        # Invalid treatment
        bad_art = dict(valid_upgraded_brief)
        bad_art["art_direction"] = {"treatment": "invalid_treatment_type"}
        errs = validate_creative_brief(bad_art)
        self.assertTrue(any("art_direction.treatment" in e for e in errs))

        # Invalid motion intensity
        bad_motion = dict(valid_upgraded_brief)
        bad_motion["motion_intensity"] = "ultra_hyper_speed"
        errs = validate_creative_brief(bad_motion)
        self.assertTrue(any("motion_intensity" in e for e in errs))

        # Invalid personal signature type
        bad_sig = dict(valid_upgraded_brief)
        bad_sig["personal_signature"] = {"type": "flamboyant_dance"}
        errs = validate_creative_brief(bad_sig)
        self.assertTrue(any("personal_signature.type" in e for e in errs))

        # Invalid evidence verification status
        bad_ev = dict(valid_upgraded_brief)
        bad_ev["evidence"] = [{"source_url": "https://example.com", "retrieved_at": "2026-10-18", "note": "test", "verification_status": "fabricated"}]
        errs = validate_creative_brief(bad_ev)
        self.assertTrue(any("verification_status" in e for e in errs))

    def test_contrast_ratio_calculation(self):
        from src.renderer.validator import calculate_contrast_ratio
        # Black and white is 21.0
        self.assertEqual(calculate_contrast_ratio("#000000", "#ffffff"), 21.0)
        # Identical colors is 1.0
        self.assertEqual(calculate_contrast_ratio("#ffffff", "#ffffff"), 1.0)
        # Ink (#171820) and Paper (#F6F0E6) is > 15:1
        ratio = calculate_contrast_ratio("#171820", "#F6F0E6")
        self.assertGreater(ratio, 15.0)

    def test_audit_creative_direction(self):
        from src.renderer.validator import audit_creative_direction
        spec = {
            "title": "Audit Test",
            "profile": "kinetic_editorial",
            "scenes": [
                {"id": "s1", "type": "title", "duration": 6.0, "headline": "Test 1", "focal_point": "Title focal point"},
                {"id": "s2", "type": "conclusion", "duration": 6.0, "headline": "Test 2", "focal_point": "Conclusion focal point"}
            ]
        }
        brief = {
            "visual_mood": "High energy",
            "palette": {"background": "#F6F0E6", "foreground": "#171820"},
            "approval": {"status": "approved"}
        }
        profile = {
            "colors": {"background": "#F6F0E6", "foreground": "#171820"},
            "layout": {"padding_x": 72, "padding_y": 140}
        }
        res = audit_creative_direction(spec, brief, profile)
        self.assertTrue(res["passed"])
        self.assertEqual(res["warnings"], [])

        # Low contrast warning
        low_contrast_brief = {
            "palette": {"background": "#e0e0e0", "foreground": "#ffffff"}
        }
        res_warn = audit_creative_direction(spec, low_contrast_brief, profile)
        self.assertFalse(res_warn["passed"])
        self.assertTrue(any("contrast ratio" in w for w in res_warn["warnings"]))


if __name__ == "__main__":
    unittest.main()
