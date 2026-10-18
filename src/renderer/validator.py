"""Validation utilities for content specifications, creative briefs, and art-direction profiles."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.scenes.registry import SCENE_REGISTRY


class ValidationError(Exception):
    """Raised when a content specification, creative brief, or profile fails validation."""
    pass


def load_profile(profile_id: str, profiles_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load profile JSON file by profile ID or filename."""
    if profiles_dir is None:
        profiles_dir = Path("config/profiles")

    # Handle direct path or profile identifier
    if profile_id.endswith(".json"):
        profile_path = Path(profile_id)
        if not profile_path.is_file():
            profile_path = profiles_dir / profile_id
    else:
        profile_path = profiles_dir / f"{profile_id}.json"

    if not profile_path.is_file():
        available = [p.stem for p in profiles_dir.glob("*.json")] if profiles_dir.is_dir() else []
        raise ValidationError(
            f"Profile '{profile_id}' not found at '{profile_path}'. "
            f"Available profiles: {', '.join(available) if available else 'none'}"
        )

    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile_data = json.load(f)
    except Exception as e:
        raise ValidationError(f"Failed to parse profile JSON '{profile_path}': {e}") from e

    # Basic profile structural sanity checks
    for section in ("colors", "typography", "layout"):
        if section not in profile_data:
            raise ValidationError(f"Profile '{profile_id}' is missing required section '{section}'")

    return profile_data


def load_creative_brief(brief_source: Any, base_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load creative brief from dict or file path."""
    if isinstance(brief_source, dict):
        return brief_source
    if isinstance(brief_source, (str, Path)):
        brief_path = Path(brief_source)
        if not brief_path.is_file() and base_dir:
            brief_path = base_dir / brief_source
        if not brief_path.is_file():
            raise ValidationError(f"Creative brief file not found: {brief_path}")
        try:
            with open(brief_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise ValidationError(f"Failed to parse creative brief JSON '{brief_path}': {e}") from e
    raise ValidationError(f"Invalid creative brief source: {type(brief_source)}")


def validate_creative_brief(brief: Dict[str, Any], require_approval: bool = True) -> List[str]:
    """Validate creative brief structure, evidence, and human approval status.

    Returns a list of validation error messages.
    """
    errors: List[str] = []

    # Required brief metadata
    for field in ("visual_mood", "pacing", "transitions", "rationale", "approval"):
        if field not in brief or not brief[field]:
            errors.append(f"Creative brief is missing required field '{field}'")

    approval = brief.get("approval", {})
    if isinstance(approval, dict):
        status = approval.get("status")
        valid_statuses = ("approved", "pending_review", "draft", "rejected")
        if status not in valid_statuses:
            errors.append(
                f"Creative brief approval status '{status}' is invalid. "
                f"Must be one of: {', '.join(valid_statuses)}"
            )
        elif require_approval and status != "approved":
            errors.append(
                f"Creative brief approval status is '{status}'. "
                "Human approval is required before final rendering. "
                "Review the brief and set approval.status to 'approved'."
            )
    else:
        errors.append("Creative brief 'approval' must be an object with 'status'")

    # Validate evidence if provided
    evidence_list = brief.get("evidence", [])
    if evidence_list:
        if not isinstance(evidence_list, list):
            errors.append("Creative brief 'evidence' must be a list of sources")
        else:
            for idx, item in enumerate(evidence_list):
                if not isinstance(item, dict):
                    errors.append(f"Evidence item {idx} must be an object")
                    continue
                for req in ("source_url", "retrieved_at", "note"):
                    if req not in item or not str(item[req]).strip():
                        errors.append(f"Evidence item {idx} is missing '{req}'")
                v_stat = item.get("verification_status")
                if not v_stat:
                    errors.append(f"Evidence item {idx} is missing 'verification_status'")
                elif v_stat not in ("verified", "unverified", "contested"):
                    errors.append(f"Evidence item {idx} verification_status '{v_stat}' is invalid")

    # Validate art direction if provided
    art_dir = brief.get("art_direction")
    if art_dir and isinstance(art_dir, dict):
        treatment = art_dir.get("treatment")
        valid_treatments = (
            "kinetic_editorial",
            "investigative",
            "data_driven",
            "documentary",
            "playful_explanatory",
            "experimental",
        )
        if treatment and treatment not in valid_treatments:
            errors.append(
                f"Creative brief art_direction.treatment '{treatment}' is invalid. "
                f"Must be one of: {', '.join(valid_treatments)}"
            )

    # Validate motion intensity if provided
    motion = brief.get("motion_intensity")
    valid_motions = ("subtle", "measured", "moderate", "high", "kinetic")
    if motion and motion not in valid_motions:
        errors.append(
            f"Creative brief motion_intensity '{motion}' is invalid. "
            f"Must be one of: {', '.join(valid_motions)}"
        )

    # Validate personal signature if provided
    sig = brief.get("personal_signature")
    if sig and isinstance(sig, dict):
        sig_type = sig.get("type")
        valid_sig_types = (
            "dry_aside",
            "understated_observation",
            "surprising_connection",
            "deliberate_pause",
            "visual_metaphor",
            "thoughtful_exit",
        )
        if sig_type and sig_type not in valid_sig_types:
            errors.append(
                f"Creative brief personal_signature.type '{sig_type}' is invalid. "
                f"Must be one of: {', '.join(valid_sig_types)}"
            )

    # Validate mobile safe area if provided
    safe_area = brief.get("mobile_safe_area")
    if safe_area:
        if not isinstance(safe_area, dict):
            errors.append("Creative brief 'mobile_safe_area' must be an object")
        else:
            for dim in ("top", "bottom", "sides"):
                val = safe_area.get(dim)
                if val is not None and (not isinstance(val, int) or val < 0):
                    errors.append(f"Creative brief mobile_safe_area.{dim} must be a non-negative integer")

    return errors


def merge_creative_direction(
    base_profile: Dict[str, Any],
    brief: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Overlay creative brief customizations onto the base profile,

    allowing each video to support its own creative direction while
    using the base profile as a starting point.
    """
    if not brief:
        return base_profile

    # Deep copy base profile dictionary
    resolved = json.loads(json.dumps(base_profile))

    # Override colors if palette is provided in brief
    brief_palette = brief.get("palette", {})
    if isinstance(brief_palette, dict) and brief_palette:
        resolved.setdefault("colors", {}).update(brief_palette)

    # Override typography if provided in brief
    brief_typo = brief.get("typography", {})
    if isinstance(brief_typo, dict) and brief_typo:
        resolved.setdefault("typography", {}).update(brief_typo)

    # Support mobile safe area overrides
    safe_area = brief.get("mobile_safe_area")
    if safe_area and isinstance(safe_area, dict):
        resolved.setdefault("layout", {})["mobile_safe_area"] = safe_area
        if "sides" in safe_area:
            resolved["layout"]["padding_x"] = max(resolved["layout"].get("padding_x", 72), safe_area["sides"])
        if "top" in safe_area:
            resolved["layout"]["padding_y"] = max(resolved["layout"].get("padding_y", 120), safe_area["top"])

    # Attach comprehensive brief metadata to resolved profile
    resolved["_creative_brief"] = {
        "visual_mood": brief.get("visual_mood"),
        "pacing": brief.get("pacing"),
        "transitions": brief.get("transitions"),
        "sound_design": brief.get("sound_design"),
        "music_recommendation": brief.get("music_recommendation"),
        "approval": brief.get("approval"),
        "story_premise": brief.get("story_premise"),
        "target_audience": brief.get("target_audience"),
        "curiosity_question": brief.get("curiosity_question"),
        "emotional_progression": brief.get("emotional_progression"),
        "opening_hook": brief.get("opening_hook"),
        "art_direction": brief.get("art_direction"),
        "motion_intensity": brief.get("motion_intensity"),
        "scene_focal_points": brief.get("scene_focal_points"),
        "personal_signature": brief.get("personal_signature"),
        "accessibility": brief.get("accessibility"),
        "narration": brief.get("narration"),
    }

    return resolved


def _parse_hex_color(hex_color: str) -> Tuple[int, int, int]:
    """Parse hex color string to RGB integers."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join([c * 2 for c in h])
    elif len(h) != 6:
        return (255, 255, 255)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def calculate_contrast_ratio(color1_hex: str, color2_hex: str) -> float:
    """Calculate WCAG 2.1 relative luminance contrast ratio between two hex colors.

    Returns a float >= 1.0 (e.g. 7.5 for 7.5:1).
    """
    def _rel_luminance(rgb: Tuple[int, int, int]) -> float:
        linear = []
        for c in rgb:
            s = c / 255.0
            linear.append(s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4)
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    rgb1 = _parse_hex_color(color1_hex)
    rgb2 = _parse_hex_color(color2_hex)
    l1 = _rel_luminance(rgb1)
    l2 = _rel_luminance(rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def audit_creative_direction(
    spec_data: Dict[str, Any],
    brief_data: Optional[Dict[str, Any]] = None,
    profile_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Evaluate creative quality, UX/psychology principles, and mobile constraints.

    Provides non-blocking warnings and recommendations for human review.
    """
    warnings: List[str] = []
    info: Dict[str, Any] = {}

    brief = brief_data or spec_data.get("creative_brief") or {}
    profile = profile_data or {}
    colors = profile.get("colors", {})
    if brief.get("palette"):
        colors = {**colors, **brief.get("palette", {})}

    # 1. Contrast & Readability Check
    bg = colors.get("background", "#ffffff")
    fg = colors.get("foreground", "#000000")
    contrast = calculate_contrast_ratio(bg, fg)
    info["foreground_contrast_ratio"] = contrast
    if contrast < 4.5:
        warnings.append(
            f"Foreground contrast ratio ({contrast}:1) is below WCAG AA recommended 4.5:1 for mobile body text."
        )

    # 2. Safe Area Clearance Check
    layout = profile.get("layout", {})
    pad_y = layout.get("padding_y", 120)
    pad_x = layout.get("padding_x", 72)
    info["pad_x"] = pad_x
    info["pad_y"] = pad_y
    if pad_y < 120:
        warnings.append(
            f"Top/bottom padding ({pad_y}px) is under 120px; platform UI overlays (Reels/Shorts) may obscure content."
        )
    if pad_x < 60:
        warnings.append(
            f"Side padding ({pad_x}px) is under 60px; right-hand engagement buttons may overlap copy."
        )

    # 3. Singular Focal Point Check
    scenes = spec_data.get("scenes", [])
    scenes_without_focal = [
        s.get("id", f"scene_{i}")
        for i, s in enumerate(scenes)
        if not s.get("focal_point")
    ]
    brief_focal_points = brief.get("scene_focal_points", [])
    if scenes_without_focal and not brief_focal_points:
        info["scenes_without_declared_focal_point"] = scenes_without_focal
        warnings.append(
            f"{len(scenes_without_focal)} scene(s) have no declared focal point. "
            "Ensure each scene establishes one dominant visual hierarchy focal point."
        )

    # 4. Narrative Arc & Pacing
    total_duration = sum(s.get("duration", 0.0) for s in scenes)
    info["total_duration"] = total_duration
    info["scene_count"] = len(scenes)
    if total_duration < 10.0:
        warnings.append("Total duration is under 10s; story arc may lack sufficient context or development.")
    elif total_duration > 65.0:
        warnings.append("Total duration exceeds 65s; retention on Reels/Shorts typically peaks under 60s.")

    # 5. Evidence & Traceability Check
    evidence_list = brief.get("evidence", [])
    unverified = [
        item.get("source_url", "unknown")
        for item in evidence_list
        if item.get("verification_status") in ("unverified", "contested")
    ]
    if unverified:
        info["unverified_evidence"] = unverified
        warnings.append(f"{len(unverified)} source citation(s) are unverified or contested.")

    # 6. Personal Signature Presence
    sig = brief.get("personal_signature") or {}
    has_scene_sig = any("personal_signature" in s for s in scenes)
    info["personal_signature_configured"] = bool(sig.get("enabled") or has_scene_sig)

    return {
        "passed": len(warnings) == 0,
        "warnings": warnings,
        "info": info,
    }


def validate_spec(spec_data: Dict[str, Any], require_approval: bool = True) -> List[str]:
    """Validate content specification dictionary for 9:16 vertical rendering.

    Returns a list of validation error messages, or an empty list if valid.
    """
    errors: List[str] = []

    # Required top-level fields
    for field in ("title", "profile", "scenes"):
        if field not in spec_data or not spec_data[field]:
            errors.append(f"Top-level field '{field}' is required and cannot be empty")

    # Output dimensions validation (defaults to 1080x1920 9:16 vertical Reels/Shorts)
    output_cfg = spec_data.get("output", {})
    if output_cfg:
        w = output_cfg.get("width", 1080)
        h = output_cfg.get("height", 1920)
        fps = output_cfg.get("fps", 30)

        if not isinstance(w, int) or w <= 0 or w % 2 != 0:
            errors.append(f"Output width must be a positive even integer, got {w}")
        if not isinstance(h, int) or h <= 0 or h % 2 != 0:
            errors.append(f"Output height must be a positive even integer, got {h}")
        if not (isinstance(fps, (int, float)) and fps > 0):
            errors.append(f"Output fps must be a positive number, got {fps}")

    # Validate creative brief if embedded or referenced
    brief_source = spec_data.get("creative_brief")
    if brief_source:
        try:
            brief_data = load_creative_brief(brief_source)
            brief_errors = validate_creative_brief(brief_data, require_approval=require_approval)
            errors.extend(brief_errors)
        except ValidationError as e:
            errors.append(str(e))
    elif require_approval:
        errors.append(
            "Top-level field 'creative_brief' is required when approval is enforced. "
            "Add a brief and obtain human approval before final rendering."
        )

    # Scenes validation
    scenes = spec_data.get("scenes", [])
    if not isinstance(scenes, list) or len(scenes) == 0:
        errors.append("Spec must contain at least one scene in 'scenes' array")
    else:
        for i, scene in enumerate(scenes):
            scene_ref = scene.get("id", f"scene_{i}")

            scene_type = scene.get("type")
            if not scene_type:
                errors.append(f"Scene '{scene_ref}' (index {i}) is missing 'type'")
            elif scene_type.strip().lower() not in SCENE_REGISTRY:
                valid_types = ", ".join(sorted(SCENE_REGISTRY.keys()))
                errors.append(
                    f"Scene '{scene_ref}' (index {i}) has unsupported type '{scene_type}'. "
                    f"Supported types: {valid_types}"
                )

            duration = scene.get("duration")
            if duration is None:
                errors.append(f"Scene '{scene_ref}' (index {i}) is missing 'duration'")
            elif not isinstance(duration, (int, float)) or duration <= 0:
                errors.append(
                    f"Scene '{scene_ref}' (index {i}) duration must be a positive number, got {duration}"
                )

            headline = scene.get("headline")
            if not headline or not str(headline).strip():
                errors.append(f"Scene '{scene_ref}' (index {i}) is missing 'headline'")

            if scene_type in ("data_chart", "chart"):
                dps = scene.get("data_points")
                if dps is not None and not isinstance(dps, list):
                    errors.append(f"Scene '{scene_ref}' 'data_points' must be a list")

    return errors
