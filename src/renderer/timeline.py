"""Frame-based scene timing and deterministic motion transforms.

This is the first rendering-timeline layer: scene frame ranges are explicit and
motion presets generate distinct frames. Audio/caption tracks can build on the
same frame clock in a later change.
"""

from dataclasses import dataclass
import math
from typing import Any, Dict, List, Sequence

from PIL import Image

SUPPORTED_MOTION_PRESETS = {"static", "push_in", "pull_out", "pan_left", "pan_right"}


@dataclass(frozen=True)
class TimelineSegment:
    """A scene's half-open frame range in the final video."""

    scene_index: int
    start_frame: int
    frame_count: int
    duration_seconds: float

    @property
    def end_frame(self) -> int:
        """Exclusive end frame."""
        return self.start_frame + self.frame_count


def build_timeline(scenes: Sequence[Dict[str, Any]], fps: float) -> List[TimelineSegment]:
    """Build a contiguous, zero-based frame schedule for ordered scenes."""
    if not isinstance(fps, (int, float)) or not math.isfinite(fps) or fps <= 0:
        raise ValueError("fps must be a positive finite number")
    if not scenes:
        raise ValueError("at least one scene is required")

    segments: List[TimelineSegment] = []
    cursor = 0
    for index, scene in enumerate(scenes):
        duration = scene.get("duration")
        if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
            raise ValueError(f"scene {index} duration must be a positive finite number")
        frame_count = max(1, round(duration * fps))
        segments.append(TimelineSegment(index, cursor, frame_count, float(duration)))
        cursor += frame_count
    return segments


def apply_motion(
    image: Image.Image,
    preset: str = "static",
    progress: float = 0.0,
    strength: float = 0.08,
) -> Image.Image:
    """Return a motion frame using a crop/scale transform.

    progress is clamped to [0, 1]. strength is a fractional zoom, capped at 25%
    by contract to avoid accidental extreme crops. Static frames are returned
    as copies so callers cannot mutate a cached scene image.
    """
    if preset not in SUPPORTED_MOTION_PRESETS:
        raise ValueError(f"Unsupported motion preset '{preset}'. Choose from: {', '.join(sorted(SUPPORTED_MOTION_PRESETS))}")
    if not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 0.25:
        raise ValueError("motion strength must be between 0 and 0.25")
    t = min(1.0, max(0.0, float(progress)))
    if preset == "static" or strength == 0:
        return image.copy()

    width, height = image.size
    if preset == "push_in":
        scale = 1.0 + strength * t
        x_fraction = y_fraction = 0.5
    elif preset == "pull_out":
        scale = 1.0 + strength * (1.0 - t)
        x_fraction = y_fraction = 0.5
    else:
        scale = 1.0 + strength
        y_fraction = 0.5
        # Camera pan direction: move the viewport across the oversized frame.
        x_fraction = 1.0 - t if preset == "pan_left" else t

    scaled_w = max(width, round(width * scale))
    scaled_h = max(height, round(height * scale))
    resized = image.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
    max_x = scaled_w - width
    max_y = scaled_h - height
    left = round(max_x * x_fraction)
    top = round(max_y * y_fraction)
    return resized.crop((left, top, left + width, top + height))
