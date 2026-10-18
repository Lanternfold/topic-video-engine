"""Burned-in, time-coded caption rendering for scene-relative caption tracks."""

from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw

from src.scenes.fonts import get_font


def active_caption(
    captions: List[Dict[str, Any]],
    elapsed_seconds: float,
) -> Optional[str]:
    """Return the text active at elapsed_seconds, using half-open [start, end) intervals."""
    for caption in captions:
        if caption["start"] <= elapsed_seconds < caption["end"]:
            return caption["text"]
    return None


def _wrap_text(text: str, draw: ImageDraw.ImageDraw, font: Any, max_width: int) -> List[str]:
    lines: List[str] = []
    for paragraph in text.splitlines() or [text]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def draw_caption(
    image: Image.Image,
    text: str,
    bottom_safe_area: int = 180,
    side_safe_area: int = 72,
) -> Image.Image:
    """Draw a legible caption in a translucent rounded box above the bottom safe area."""
    if not text.strip():
        return image.copy()
    base = image.convert("RGBA")
    width, height = base.size
    font_size = max(18, min(54, round(width * 0.045)))
    font = get_font(["Arial Bold", "Helvetica Neue", "DejaVuSans-Bold", "Arial"], font_size)
    draw = ImageDraw.Draw(base)
    max_text_width = max(1, width - 2 * max(0, side_safe_area) - 48)
    lines = _wrap_text(text, draw, font, max_text_width)
    line_heights = [
        max(1, draw.textbbox((0, 0), line or "Ag", font=font)[3] - draw.textbbox((0, 0), line or "Ag", font=font)[1])
        for line in lines
    ]
    line_gap = max(4, font_size // 5)
    text_height = sum(line_heights) + line_gap * (len(lines) - 1)
    pad_x = max(12, font_size // 2)
    pad_y = max(8, font_size // 3)
    box_width = min(width - 2 * max(0, side_safe_area), max(
        (draw.textbbox((0, 0), line, font=font)[2] for line in lines), default=0
    ) + 2 * pad_x)
    box_height = text_height + 2 * pad_y
    left = (width - box_width) // 2
    bottom = height - max(0, bottom_safe_area)
    top = max(0, bottom - box_height)
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rounded_rectangle(
        (left, top, left + box_width, bottom),
        radius=max(8, font_size // 4),
        fill=(0, 0, 0, 205),
    )
    y = top + pad_y
    for line, line_height in zip(lines, line_heights):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) // 2
        odraw.text((x, y), line, font=font, fill=(255, 255, 255, 255), stroke_width=0)
        y += line_height + line_gap
    return Image.alpha_composite(base, overlay).convert("RGB")
