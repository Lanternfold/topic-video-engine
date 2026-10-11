"""Core rendering engine for Topic Video Engine.

Sequences scene components, renders frames via Pillow, and encodes 9:16 MP4 via FFmpeg.
"""

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, Optional

# Ensure repository root is on sys.path when invoked directly as a script
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.renderer.ffmpeg_writer import FFmpegWriter
from src.renderer.validator import (
    ValidationError,
    load_creative_brief,
    load_profile,
    merge_creative_direction,
    validate_spec,
)
from src.scenes.registry import get_scene_renderer


def render_video(
    spec_path: Path,
    output_path: Optional[Path] = None,
    profiles_dir: Optional[Path] = None,
    brief_override: Optional[Path] = None,
    require_approval: bool = True,
    verbose: bool = True,
) -> Path:
    """Render a video from a content specification JSON file.

    Args:
        spec_path: Path to content specification JSON.
        output_path: Optional destination MP4 path. If omitted, uses spec output configuration or defaults to output/.
        profiles_dir: Optional directory containing profile JSON files.
        brief_override: Optional external creative brief JSON file path.
        require_approval: Whether to enforce human approval status on creative brief before rendering.
        verbose: Whether to print progress messages to stdout.

    Returns:
        Path to generated MP4 video file.
    """
    spec_path = Path(spec_path)
    if not spec_path.is_file():
        raise FileNotFoundError(f"Content specification file not found: {spec_path}")

    # Load and validate content specification
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            spec_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in spec file '{spec_path}': {e}") from e

    errors = validate_spec(spec_data, require_approval=require_approval)
    if errors:
        error_details = "\n  - " + "\n  - ".join(errors)
        raise ValidationError(f"Content specification failed validation:{error_details}")

    profile_id = spec_data["profile"]
    base_profile_data = load_profile(profile_id, profiles_dir=profiles_dir)

    # Resolve creative brief if specified in spec or overridden via CLI
    brief_data = None
    if brief_override:
        brief_data = load_creative_brief(brief_override)
    elif "creative_brief" in spec_data:
        brief_data = load_creative_brief(spec_data["creative_brief"], base_dir=spec_path.parent)

    # Merge creative brief customizations with base profile
    profile_data = merge_creative_direction(base_profile_data, brief_data)

    output_cfg = spec_data.get("output", {})
    width = int(output_cfg.get("width", 1080))
    height = int(output_cfg.get("height", 1920))
    fps = int(output_cfg.get("fps", 30))

    # Resolve final output path
    if output_path is None:
        target_name = output_cfg.get("filename")
        if not target_name:
            safe_title = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in spec_data.get("title", "video"))
            target_name = f"{safe_title.lower()}_{profile_id}.mp4"
        output_path = Path("output") / target_name
    else:
        output_path = Path(output_path)

    scenes = spec_data.get("scenes", [])
    total_duration = sum(s.get("duration", 0.0) for s in scenes)
    total_expected_frames = sum(max(1, round(s.get("duration", 0.0) * fps)) for s in scenes)

    if verbose:
        print(f"[Engine] Rendering '{spec_data.get('title')}'")
        print(f"[Engine] Base Profile: {base_profile_data.get('name', profile_id)} ({profile_id})")
        if brief_data:
            appr = brief_data.get("approval", {})
            print(f"[Engine] Creative Mood: {brief_data.get('visual_mood', 'N/A')}")
            print(f"[Engine] Approval: {appr.get('status')} by {appr.get('approved_by', 'unassigned')}")
        print(f"[Engine] Format: {width}x{height} (9:16) @ {fps}fps, ~{total_duration:.1f}s")
        print(f"[Engine] Scenes: {len(scenes)}, expected frames: {total_expected_frames}")

    start_time = time.time()

    with FFmpegWriter(output_path, width=width, height=height, fps=fps) as writer:
        for idx, scene in enumerate(scenes):
            scene_id = scene.get("id", f"scene_{idx}")
            scene_type = scene.get("type", "unknown")
            duration = float(scene.get("duration", 1.0))
            frame_count = max(1, round(duration * fps))

            if verbose:
                print(f"  [{idx+1}/{len(scenes)}] Rendering '{scene_id}' ({scene_type}, {duration:.1f}s -> {frame_count} frames)...")

            renderer = get_scene_renderer(scene_type, profile=profile_data, width=width, height=height)
            frame_img = renderer.render(scene)

            # Stream static scene frames to FFmpeg
            writer.write_frame_repeated(frame_img, frame_count)

    elapsed = time.time() - start_time
    file_size_kb = output_path.stat().st_size / 1024

    if verbose:
        print(f"[Engine] Successfully generated {output_path} ({file_size_kb:.1f} KB in {elapsed:.2f}s)")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Topic Video Engine 9:16 vertical renderer")
    parser.add_argument("--spec", "-s", required=True, type=Path, help="Path to content specification JSON")
    parser.add_argument("--output", "-o", type=Path, help="Custom output MP4 path")
    parser.add_argument("--profiles-dir", type=Path, help="Custom directory containing art-direction profiles")
    parser.add_argument("--brief", "-b", type=Path, help="Custom creative brief JSON path")
    parser.add_argument(
        "--allow-unapproved",
        action="store_true",
        help="Allow rendering even if creative brief approval status is pending/draft (for preview drafting)"
    )

    args = parser.parse_args()

    try:
        out_path = render_video(
            spec_path=args.spec,
            output_path=args.output,
            profiles_dir=args.profiles_dir,
            brief_override=args.brief,
            require_approval=not args.allow_unapproved,
        )
        print(f"Video saved to: {out_path}")
    except (ValidationError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected rendering error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
