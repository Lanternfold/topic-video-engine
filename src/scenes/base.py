"""Base scene class and drawing primitives for Topic Video Engine."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from src.scenes.fonts import get_font


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string (#rgb, #rrggbb) to RGB tuple."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join([c * 2 for c in h])
    elif len(h) != 6:
        return (255, 255, 255)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> List[str]:
    """Wrap text to fit within max_width using font metrics."""
    if not text:
        return []
    words = text.split(" ")
    lines: List[str] = []
    current_line = words[0]

    for word in words[1:]:
        test_line = f"{current_line} {word}"
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)
    return lines


class BaseScene(ABC):
    """Abstract base scene renderer."""

    def __init__(self, profile: Dict[str, Any], width: int = 1080, height: int = 1920):
        self.profile = profile
        self.width = width
        self.height = height
        self.colors = profile.get("colors", {})
        self.typography = profile.get("typography", {})
        self.layout = profile.get("layout", {})
        self.components = profile.get("components", {})

        # Resolve primary fonts
        families = self.typography.get("font_families", ["Menlo", "Courier"])
        sans_families = self.typography.get("sans_font_families", ["Helvetica Neue", "Arial", "sans-serif"])

        self.font_title = get_font(families, self.typography.get("title_size", 56))
        self.font_headline = get_font(families, self.typography.get("headline_size", 42))
        self.font_subtitle = get_font(families, self.typography.get("subtitle_size", 26))
        self.font_body = get_font(families, self.typography.get("body_size", 22))
        self.font_code = get_font(["Menlo", "SF Pro Mono", "Monaco", "Courier New"], self.typography.get("code_size", 22))
        self.font_caption = get_font(sans_families if "sans_font_families" in self.typography else families, self.typography.get("caption_size", 18))
        self.font_badge = get_font(sans_families if "sans_font_families" in self.typography else families, self.typography.get("badge_size", 16))
        self.font_metric = get_font(families, self.typography.get("metric_size", 80))

        # Layout parameters with mobile safe area awareness (Reels & Shorts platform overlays)
        safe_area = self.layout.get("mobile_safe_area") or self.profile.get("_creative_brief", {}).get("mobile_safe_area") or {}
        self.safe_top = safe_area.get("top", 120)
        self.safe_bottom = safe_area.get("bottom", 160)
        self.safe_sides = safe_area.get("sides", 72)

        self.pad_x = max(self.layout.get("padding_x", 120), self.safe_sides)
        self.pad_y = max(self.layout.get("padding_y", 80), self.safe_top)
        self.card_pad = self.layout.get("card_padding", 36)
        self.border_radius = self.layout.get("border_radius", 8)
        self.line_spacing = self.layout.get("line_spacing", 10)

    def get_semantic_color(self, role: str, fallback_hex: Optional[str] = None) -> Tuple[int, int, int]:
        """Resolve semantic role color (defect, discovery, validation, warning, etc.)."""
        semantic_map = self.colors.get("semantic_roles", {})
        if not semantic_map and "_creative_brief" in self.profile:
            palette = self.profile["_creative_brief"].get("palette", {})
            semantic_map = palette.get("semantic_roles", {})

        if role in semantic_map:
            return hex_to_rgb(semantic_map[role])
        if role in self.colors:
            return hex_to_rgb(self.colors[role])
        if fallback_hex:
            return hex_to_rgb(fallback_hex)
        return hex_to_rgb(self.colors.get("accent", "#FF5C35"))

    def draw_personal_signature(self, draw: ImageDraw.ImageDraw, signature_text: str, y_pos: Optional[int] = None) -> int:
        """Render understated creator personal signature (~5% subtle fingerprint)."""
        if not signature_text:
            return y_pos or (self.height - self.safe_bottom)

        curr_y = y_pos if y_pos is not None else (self.height - self.safe_bottom - 50)
        max_w = self.width - 2 * self.pad_x

        accent_color = hex_to_rgb(self.colors.get("accent_secondary", self.colors.get("accent", "#FFD447")))
        card_bg = hex_to_rgb(self.colors.get("card_bg", "#FFFFFF"))
        card_border = hex_to_rgb(self.colors.get("card_border", "#D8CFBE"))
        text_color = hex_to_rgb(self.colors.get("secondary", "#3D4050"))

        lines = wrap_text(signature_text, self.font_caption, max_w - 60, draw)
        lh = 24
        box_h = len(lines) * lh + 20

        # Draw subtle callout capsule
        draw.rounded_rectangle(
            [self.pad_x, curr_y, self.width - self.pad_x, curr_y + box_h],
            radius=4,
            fill=card_bg,
            outline=card_border,
            width=1
        )
        # Left subtle accent bar
        draw.rectangle(
            [self.pad_x, curr_y, self.pad_x + 5, curr_y + box_h],
            fill=accent_color
        )

        draw.text((self.pad_x + 16, curr_y + 10), "◆", fill=accent_color, font=self.font_caption)

        line_y = curr_y + 10
        for line in lines:
            draw.text((self.pad_x + 36, line_y), line, fill=text_color, font=self.font_caption)
            line_y += lh

        return curr_y + box_h

    def create_canvas(self) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        """Create a blank canvas pre-filled with the profile's background color."""
        bg_color = hex_to_rgb(self.colors.get("background", "#0d1117"))
        img = Image.new("RGB", (self.width, self.height), bg_color)
        draw = ImageDraw.Draw(img)
        return img, draw

    def draw_header(
        self,
        draw: ImageDraw.ImageDraw,
        headline: str,
        tag: Optional[str] = None,
        supporting_text: Optional[str] = None,
        top_offset: Optional[int] = None
    ) -> int:
        """Render standard top header with profile-specific aesthetic flair (dots vs rules).

        Returns the Y position immediately following the header.
        """
        curr_y = top_offset if top_offset is not None else self.pad_y
        header_style = self.layout.get("header_style", "terminal_dots")
        accent_color = hex_to_rgb(self.colors.get("accent", "#38bdf8"))
        foreground_color = hex_to_rgb(self.colors.get("foreground", "#e6edf3"))
        secondary_color = hex_to_rgb(self.colors.get("secondary", "#8b949e"))
        card_border_color = hex_to_rgb(self.colors.get("card_border", "#30363d"))

        # Header aesthetic variation
        if header_style == "terminal_dots":
            # Developer style: Terminal dots + tag
            # Three dots
            dot_radius = 6
            dot_spacing = 18
            dot_colors = [(239, 68, 68), (234, 179, 8), (34, 197, 94)]  # red, yellow, green
            for i, col in enumerate(dot_colors):
                cx = self.pad_x + i * dot_spacing
                cy = curr_y + 8
                draw.ellipse([cx - dot_radius, cy - dot_radius, cx + dot_radius, cy + dot_radius], fill=col)

            badge_x = self.pad_x + 3 * dot_spacing + 16
            if tag:
                badge_bg = hex_to_rgb(self.colors.get("badge_bg", "#1f2937"))
                badge_text_color = hex_to_rgb(self.colors.get("badge_text", "#38bdf8"))
                tb = draw.textbbox((badge_x, curr_y), tag, font=self.font_badge)
                # Draw rounded badge
                draw.rounded_rectangle(
                    [badge_x - 10, curr_y - 2, tb[2] + 10, tb[3] + 2],
                    radius=4,
                    fill=badge_bg,
                    outline=card_border_color,
                    width=1
                )
                draw.text((badge_x, curr_y), tag, fill=badge_text_color, font=self.font_badge)

            curr_y += 36

        elif header_style == "editorial_rule":
            # Editorial style: Eyebrow category + horizontal masthead rule
            if tag:
                draw.text((self.pad_x, curr_y), tag.upper(), fill=accent_color, font=self.font_badge)
                tb = draw.textbbox((self.pad_x, curr_y), tag.upper(), font=self.font_badge)
                curr_y = tb[3] + 10

            # Editorial horizontal rule line
            draw.line([(self.pad_x, curr_y), (self.width - self.pad_x, curr_y)], fill=accent_color, width=3)
            curr_y += 18

        elif header_style == "forensic_bracket":
            # Forensic style: Diagnostic bracket prefix + coordinate timestamp rule
            bracket_text = f"[ {tag.upper() if tag else 'AUDIT // TELEMETRY'} ]"
            draw.text((self.pad_x, curr_y), bracket_text, fill=accent_color, font=self.font_badge)
            tb = draw.textbbox((self.pad_x, curr_y), bracket_text, font=self.font_badge)
            
            # Technical scanline / hairline rule with coordinate ticks
            rule_y = tb[3] + 12
            draw.line([(self.pad_x, rule_y), (self.width - self.pad_x, rule_y)], fill=card_border_color, width=1)
            # Corner accent notch
            draw.line([(self.pad_x, rule_y - 6), (self.pad_x, rule_y + 6)], fill=accent_color, width=2)
            draw.line([(self.width - self.pad_x, rule_y - 6), (self.width - self.pad_x, rule_y + 6)], fill=accent_color, width=2)
            curr_y = rule_y + 18

        elif header_style == "cinematic_hud":
            # Cinematic style: Luminous status pill + glowing hairline
            if tag:
                pill_x = self.pad_x
                # Luminous dot
                dot_r = 5
                draw.ellipse([pill_x, curr_y + 6 - dot_r, pill_x + 2 * dot_r, curr_y + 6 + dot_r], fill=accent_color)
                draw.text((pill_x + 18, curr_y), tag.upper(), fill=foreground_color, font=self.font_badge)
                tb = draw.textbbox((pill_x + 18, curr_y), tag.upper(), font=self.font_badge)
                curr_y = tb[3] + 14

            # Subtle glow rule
            draw.line([(self.pad_x, curr_y), (self.pad_x + 240, curr_y)], fill=accent_color, width=2)
            draw.line([(self.pad_x + 240, curr_y), (self.width - self.pad_x, curr_y)], fill=card_border_color, width=1)
            curr_y += 20

        # Draw Headline
        max_w = self.width - 2 * self.pad_x
        headline_lines = wrap_text(headline, self.font_headline, max_w, draw)
        for line in headline_lines:
            draw.text((self.pad_x, curr_y), line, fill=foreground_color, font=self.font_headline)
            tb = draw.textbbox((self.pad_x, curr_y), line, font=self.font_headline)
            curr_y = tb[3] + self.line_spacing

        # Draw Supporting Subtitle
        if supporting_text:
            curr_y += 6
            sub_lines = wrap_text(supporting_text, self.font_subtitle, max_w, draw)
            for line in sub_lines:
                draw.text((self.pad_x, curr_y), line, fill=secondary_color, font=self.font_subtitle)
                tb = draw.textbbox((self.pad_x, curr_y), line, font=self.font_subtitle)
                curr_y = tb[3] + self.line_spacing

        return curr_y + 24

    def draw_footnote(self, draw: ImageDraw.ImageDraw, footnote: str):
        """Render footnote or attribution along bottom padding."""
        if not footnote:
            return
        caption_color = hex_to_rgb(self.colors.get("muted", "#6b7280"))
        accent_color = hex_to_rgb(self.colors.get("accent", "#38bdf8"))
        tb = draw.textbbox((0, 0), footnote, font=self.font_caption)
        fh = tb[3] - tb[1]
        fy = self.height - max(self.pad_y, getattr(self, "safe_bottom", 160)) + 20

        # Small accent indicator dot or tick
        draw.rectangle([self.pad_x, fy + 4, self.pad_x + 8, fy + 12], fill=accent_color)
        draw.text((self.pad_x + 18, fy), footnote, fill=caption_color, font=self.font_caption)

    @abstractmethod
    def render(self, scene_data: Dict[str, Any]) -> Image.Image:
        """Render the scene to a PIL Image."""
        pass
