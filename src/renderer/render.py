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

from PIL import Image, ImageDraw

from src.renderer.ffmpeg_writer import FFmpegWriter
from src.renderer.timeline import apply_motion, build_timeline
from src.renderer.captions import active_caption, draw_caption
from src.renderer.validator import (
    ValidationError,
    audit_creative_direction,
    load_creative_brief,
    load_profile,
    merge_creative_direction,
    validate_spec,
)
from src.scenes.fonts import get_font
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

    # An explicit CLI brief overrides the embedded brief and must be the one validated.
    if brief_override:
        spec_data["creative_brief"] = str(brief_override)

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
    timeline = build_timeline(scenes, fps)
    total_duration = sum(segment.duration_seconds for segment in timeline)
    total_expected_frames = sum(segment.frame_count for segment in timeline)

    if verbose:
        print(f"[Engine] Rendering '{spec_data.get('title')}'")
        print(f"[Engine] Base Profile: {base_profile_data.get('name', profile_id)} ({profile_id})")
        if brief_data:
            appr = brief_data.get("approval", {})
            print(f"[Engine] Creative Mood: {brief_data.get('visual_mood', 'N/A')}")
            print(f"[Engine] Approval: {appr.get('status')} by {appr.get('approved_by', 'unassigned')}")
        print(f"[Engine] Format: {width}x{height} (9:16) @ {fps}fps, ~{total_duration:.1f}s")
        print(f"[Engine] Scenes: {len(scenes)}, expected frames: {total_expected_frames}")

    # Creative quality pre-flight audit
    audit_res = audit_creative_direction(spec_data, brief_data, profile_data)
    if verbose and audit_res["warnings"]:
        print("[Creative Audit] Pre-flight recommendations:")
        for w in audit_res["warnings"]:
            print(f"  ⚠ {w}")

    start_time = time.time()

    with FFmpegWriter(output_path, width=width, height=height, fps=fps) as writer:
        for idx, scene in enumerate(scenes):
            scene_id = scene.get("id", f"scene_{idx}")
            scene_type = scene.get("type", "unknown")
            segment = timeline[idx]
            frame_count = segment.frame_count
            motion_cfg = scene.get("motion", {})
            if isinstance(motion_cfg, str):
                motion_cfg = {"preset": motion_cfg}
            motion_preset = motion_cfg.get("preset", "static")
            motion_strength = motion_cfg.get("strength", 0.08)

            if verbose:
                print(
                    f"  [{idx+1}/{len(scenes)}] Rendering '{scene_id}' "
                    f"({scene_type}, {segment.duration_seconds:.1f}s -> {frame_count} frames, "
                    f"motion={motion_preset})..."
                )

            renderer = get_scene_renderer(scene_type, profile=profile_data, width=width, height=height)
            frame_img = renderer.render(scene)

            caption_track = scene.get("captions", [])
            if (motion_preset == "static" or motion_strength == 0) and not caption_track:
                writer.write_frame_repeated(frame_img, frame_count)
            else:
                # Motion and captions share the exact same frame clock.
                safe_area = profile_data.get("layout", {}).get("mobile_safe_area", {})
                brief_safe_area = (brief_data or {}).get("mobile_safe_area", {})
                bottom_safe = max(
                    0,
                    brief_safe_area.get("bottom", safe_area.get("bottom", 180)),
                )
                side_safe = max(
                    0,
                    brief_safe_area.get("sides", safe_area.get("sides", 72)),
                )
                for frame_index in range(frame_count):
                    progress = frame_index / max(1, frame_count - 1)
                    motion_frame = apply_motion(
                        frame_img,
                        preset=motion_preset,
                        progress=progress,
                        strength=motion_strength,
                    )
                    elapsed = frame_index / fps
                    caption_text = active_caption(caption_track, elapsed) if caption_track else None
                    if caption_text:
                        motion_frame = draw_caption(
                            motion_frame,
                            caption_text,
                            bottom_safe_area=bottom_safe,
                            side_safe_area=side_safe,
                        )
                    writer.write_frame(motion_frame)

    elapsed = time.time() - start_time
    file_size_kb = output_path.stat().st_size / 1024

    if verbose:
        print(f"[Engine] Successfully generated {output_path} ({file_size_kb:.1f} KB in {elapsed:.2f}s)")

    return output_path


def generate_contact_sheet(
    spec_path: Path,
    output_path: Optional[Path] = None,
    profiles_dir: Optional[Path] = None,
    brief_override: Optional[Path] = None,
    thumb_width: int = 360,
    thumb_height: int = 640,
) -> Path:
    """Generate a high-resolution contact sheet image showing hero frames of all scenes.

    Enables rapid creative review of narrative progression, visual hierarchy, mobile safe areas,
    and palette harmony.
    """
    spec_path = Path(spec_path)
    if not spec_path.is_file():
        raise FileNotFoundError(f"Content specification file not found: {spec_path}")

    with open(spec_path, "r", encoding="utf-8") as f:
        spec_data = json.load(f)

    profile_id = spec_data["profile"]
    base_profile_data = load_profile(profile_id, profiles_dir=profiles_dir)

    brief_data = None
    if brief_override:
        brief_data = load_creative_brief(brief_override)
    elif "creative_brief" in spec_data:
        brief_data = load_creative_brief(spec_data["creative_brief"], base_dir=spec_path.parent)

    profile_data = merge_creative_direction(base_profile_data, brief_data)

    output_cfg = spec_data.get("output", {})
    w = int(output_cfg.get("width", 1080))
    h = int(output_cfg.get("height", 1920))
    scenes = spec_data.get("scenes", [])
    if not scenes:
        raise ValidationError("Spec contains no scenes to generate contact sheet")

    # Render each scene hero frame
    rendered_frames = []
    for idx, scene in enumerate(scenes):
        scene_type = scene.get("type", "unknown")
        renderer = get_scene_renderer(scene_type, profile=profile_data, width=w, height=h)
        frame_img = renderer.render(scene)
        thumb = frame_img.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        rendered_frames.append((scene, thumb))

    num_scenes = len(rendered_frames)
    cols = min(num_scenes, 4)
    rows = (num_scenes + cols - 1) // cols

    card_margin_x = 24
    card_margin_y = 24
    info_h = 100
    top_header_h = 140

    sheet_w = cols * thumb_width + (cols + 1) * card_margin_x
    sheet_h = top_header_h + rows * (thumb_height + info_h + card_margin_y) + card_margin_y

    sheet = Image.new("RGB", (sheet_w, sheet_h), (20, 24, 30))
    draw = ImageDraw.Draw(sheet)

    font_head = get_font(["Helvetica Neue", "Arial", "sans-serif"], 32)
    font_sub = get_font(["Helvetica Neue", "Arial", "sans-serif"], 20)
    font_meta = get_font(["Menlo", "Courier"], 16)

    title_str = spec_data.get("title", "Topic Video")
    mood_str = brief_data.get("visual_mood") if brief_data else base_profile_data.get("name", profile_id)
    total_dur = sum(s.get("duration", 0.0) for s in scenes)
    draw.text((card_margin_x, 28), f"CREATIVE CONTACT SHEET // {title_str}", fill=(240, 246, 252), font=font_head)
    draw.text((card_margin_x, 72), f"Profile: {profile_id} • Mood: {mood_str}", fill=(139, 148, 158), font=font_sub)
    draw.text((card_margin_x, 102), f"Scenes: {num_scenes} • Total Duration: {total_dur:.1f}s • Target: 9:16 Vertical (1080x1920 @ 30fps)", fill=(56, 189, 248), font=font_meta)

    draw.line([(card_margin_x, top_header_h - 15), (sheet_w - card_margin_x, top_header_h - 15)], fill=(48, 54, 61), width=1)

    for i, (scene, thumb) in enumerate(rendered_frames):
        r = i // cols
        c = i % cols
        x = card_margin_x + c * (thumb_width + card_margin_x)
        y = top_header_h + r * (thumb_height + info_h + card_margin_y)

        sheet.paste(thumb, (x, y))
        draw.rectangle([x, y, x + thumb_width, y + thumb_height], outline=(56, 62, 70), width=1)

        info_y = y + thumb_height + 12
        sc_id = scene.get("id", f"scene_{i}")
        sc_type = scene.get("type", "")
        sc_dur = scene.get("duration", 0)
        focal = scene.get("focal_point") or "Singular visual focal point"

        draw.text((x, info_y), f"[{i+1}/{num_scenes}] {sc_id} ({sc_dur:.1f}s)", fill=(240, 246, 252), font=font_sub)
        draw.text((x, info_y + 26), f"Type: {sc_type}", fill=(139, 148, 158), font=font_meta)
        draw.text((x, info_y + 48), f"Focal: {focal[:35]}", fill=(56, 189, 248), font=font_meta)
        if scene.get("personal_signature"):
            draw.text((x, info_y + 70), f"◆ Aside: {scene['personal_signature'][:32]}", fill=(255, 212, 71), font=font_meta)

    if output_path is None:
        target_dir = Path("output")
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_title = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in spec_data.get("title", "contact_sheet"))
        output_path = target_dir / f"{safe_title.lower()}_contact_sheet.png"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    sheet.save(str(output_path), "PNG")
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
    parser.add_argument(
        "--contact-sheet",
        type=Path,
        nargs="?",
        const=True,
        help="Generate preview contact sheet PNG instead of full video render (optionally specify destination path)"
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Run pre-flight creative quality and UX audit without rendering"
    )

    args = parser.parse_args()

    try:
        if args.audit:
            with open(args.spec, "r", encoding="utf-8") as f:
                spec_data = json.load(f)
            prof_data = load_profile(spec_data["profile"], profiles_dir=args.profiles_dir)
            brief_data = None
            if args.brief:
                brief_data = load_creative_brief(args.brief)
            elif "creative_brief" in spec_data:
                brief_data = load_creative_brief(spec_data["creative_brief"], base_dir=args.spec.parent)

            res = audit_creative_direction(
                spec_data,
                brief_data,
                prof_data,
                require_approval=not args.allow_unapproved,
            )
            print("=== Creative Direction Audit ===")
            print(f"Status: {'PASSED' if res['passed'] else 'FAILED / REVIEW REQUIRED'}")
            for error in res.get("errors", []):
                print(f"  ✗ Validation error: {error}")
            for warning in res["warnings"]:
                print(f"  ⚠ {warning}")
            if res["passed"]:
                print("  ✓ Structural validation and creative checks passed.")
            print(f"Info: {res['info']}")
            if res.get("errors"):
                sys.exit(1)
            return

        if args.contact_sheet:
            sheet_out = None if args.contact_sheet is True else args.contact_sheet
            sheet_path = generate_contact_sheet(
                spec_path=args.spec,
                output_path=sheet_out,
                profiles_dir=args.profiles_dir,
                brief_override=args.brief,
            )
            print(f"Contact sheet saved to: {sheet_path}")
            return

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
