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
    if isinstance(brief_palette, dict):
        resolved.setdefault("colors", {}).update(brief_palette)

    # Override typography if provided in brief
    brief_typo = brief.get("typography", {})
    if isinstance(brief_typo, dict):
        resolved.setdefault("typography", {}).update(brief_typo)

    # Attach brief metadata to resolved profile
    resolved["_creative_brief"] = {
        "visual_mood": brief.get("visual_mood"),
        "pacing": brief.get("pacing"),
        "transitions": brief.get("transitions"),
        "sound_design": brief.get("sound_design"),
        "music_recommendation": brief.get("music_recommendation"),
        "approval": brief.get("approval"),
    }

    return resolved


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
