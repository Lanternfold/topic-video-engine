"""Title / Intro scene renderer."""

from typing import Any, Dict
from PIL import Image

from src.scenes.base import BaseScene, hex_to_rgb, wrap_text
from src.scenes.fonts import get_font


class TitleScene(BaseScene):
    """Renders the opening title / cover frame."""

    def render(self, scene_data: Dict[str, Any]) -> Image.Image:
        img, draw = self.create_canvas()

        headline = scene_data.get("headline", "")
        supporting_text = scene_data.get("supporting_text", "")
        tag = scene_data.get("tag", "")
        footnote = scene_data.get("footnote", "")

        header_style = self.layout.get("header_style", "terminal_dots")
        accent_color = hex_to_rgb(self.colors.get("accent", "#38bdf8"))
        foreground_color = hex_to_rgb(self.colors.get("foreground", "#e6edf3"))
        secondary_color = hex_to_rgb(self.colors.get("secondary", "#8b949e"))
        card_bg = hex_to_rgb(self.colors.get("card_bg", "#161b22"))
        card_border = hex_to_rgb(self.colors.get("card_border", "#30363d"))

        if header_style == "terminal_dots":
            # Developer aesthetic: Centered hero terminal card
            card_w = self.width - 2 * self.pad_x
            avail_h = self.height - 2 * self.pad_y
            # In 9:16 vertical, cap card height so it doesn't leave huge empty void
            card_h = min(avail_h, 1020)
            card_x0 = self.pad_x
            card_y0 = self.pad_y + (avail_h - card_h) // 2
            card_x1 = card_x0 + card_w
            card_y1 = card_y0 + card_h

            # Draw outer terminal card
            draw.rounded_rectangle(
                [card_x0, card_y0, card_x1, card_y1],
                radius=self.border_radius,
                fill=card_bg,
                outline=card_border,
                width=2
            )

            # Top window title bar
            bar_h = 48
            draw.rounded_rectangle(
                [card_x0, card_y0, card_x1, card_y0 + bar_h],
                radius=self.border_radius,
                fill=card_border
            )
            draw.rectangle(
                [card_x0, card_y0 + bar_h - 10, card_x1, card_y0 + bar_h],
                fill=card_border
            )

            # Traffic light dots
            dot_y = card_y0 + bar_h // 2
            dot_colors = [(239, 68, 68), (234, 179, 8), (34, 197, 94)]
            for i, col in enumerate(dot_colors):
                cx = card_x0 + 24 + i * 20
                draw.ellipse([cx - 5, dot_y - 5, cx + 5, dot_y + 5], fill=col)

            # Bar title
            bar_title = "session ~ video-brief.md"
            draw.text((card_x0 + 96, dot_y - 8), bar_title, fill=secondary_color, font=self.font_caption)

            # Content inside card
            inner_x = card_x0 + self.card_pad + 20
            inner_y = card_y0 + bar_h + 100
            inner_w = card_w - 2 * (self.card_pad + 20)

            # Tag badge
            if tag:
                badge_bg = hex_to_rgb(self.colors.get("badge_bg", "#1f2937"))
                badge_text_color = hex_to_rgb(self.colors.get("badge_text", "#38bdf8"))
                tb = draw.textbbox((inner_x, inner_y), tag, font=self.font_badge)
                draw.rounded_rectangle(
                    [inner_x - 12, inner_y - 6, tb[2] + 12, tb[3] + 6],
                    radius=4,
                    fill=badge_bg,
                    outline=card_border,
                    width=1
                )
                draw.text((inner_x, inner_y), tag, fill=badge_text_color, font=self.font_badge)
                inner_y = tb[3] + 44

            # Main headline
            head_lines = wrap_text(headline, self.font_title, inner_w, draw)
            for line in head_lines:
                draw.text((inner_x, inner_y), line, fill=foreground_color, font=self.font_title)
                tb = draw.textbbox((inner_x, inner_y), line, font=self.font_title)
                inner_y = tb[3] + self.line_spacing + 4

            # Subtitle
            if supporting_text:
                inner_y += 20
                sub_lines = wrap_text(supporting_text, self.font_subtitle, inner_w, draw)
                for line in sub_lines:
                    draw.text((inner_x, inner_y), line, fill=secondary_color, font=self.font_subtitle)
                    tb = draw.textbbox((inner_x, inner_y), line, font=self.font_subtitle)
                    inner_y = tb[3] + self.line_spacing

            # Prompt cursor decoration at bottom of card
            cursor_y = card_y1 - 60
            prompt_str = scene_data.get("prompt_str", "$ topic-video-engine --render --profile=developer_workflow █")
            draw.text((inner_x, cursor_y), prompt_str, fill=accent_color, font=self.font_code)

        elif header_style == "forensic_bracket":
            # Investigative / Forensic aesthetic: Diagnostic dossier card with corner brackets
            card_w = self.width - 2 * self.pad_x
            avail_h = self.height - 2 * self.pad_y
            card_h = min(avail_h, 1100)
            card_x0 = self.pad_x
            card_y0 = self.pad_y + (avail_h - card_h) // 2
            card_x1 = card_x0 + card_w
            card_y1 = card_y0 + card_h

            # Outer forensic container
            draw.rectangle(
                [card_x0, card_y0, card_x1, card_y1],
                fill=card_bg,
                outline=card_border,
                width=1
            )

            # High-tech corner bracket accents
            bracket_len = 32
            draw.line([(card_x0, card_y0), (card_x0 + bracket_len, card_y0)], fill=accent_color, width=4)
            draw.line([(card_x0, card_y0), (card_x0, card_y0 + bracket_len)], fill=accent_color, width=4)
            draw.line([(card_x1, card_y0), (card_x1 - bracket_len, card_y0)], fill=accent_color, width=4)
            draw.line([(card_x1, card_y0), (card_x1, card_y0 + bracket_len)], fill=accent_color, width=4)
            draw.line([(card_x0, card_y1), (card_x0 + bracket_len, card_y1)], fill=accent_color, width=4)
            draw.line([(card_x0, card_y1), (card_x0, card_y1 - bracket_len)], fill=accent_color, width=4)
            draw.line([(card_x1, card_y1), (card_x1 - bracket_len, card_y1)], fill=accent_color, width=4)
            draw.line([(card_x1, card_y1), (card_x1, card_y1 - bracket_len)], fill=accent_color, width=4)

            # Top forensic title bar
            bar_h = 52
            draw.rectangle([card_x0, card_y0, card_x1, card_y0 + bar_h], fill=hex_to_rgb(self.colors.get("code_bg", "#0b0f14")))
            draw.line([(card_x0, card_y0 + bar_h), (card_x1, card_y0 + bar_h)], fill=card_border, width=1)

            # Top bar status stamp
            bar_text = f"// DOSSIER_AUDIT: {tag.upper() if tag else 'DATA_INGEST_INCIDENT'} //"
            draw.text((card_x0 + 24, card_y0 + 16), bar_text, fill=accent_color, font=self.font_badge)

            # Inner content
            inner_x = card_x0 + self.card_pad + 20
            inner_y = card_y0 + bar_h + 80
            inner_w = card_w - 2 * (self.card_pad + 20)

            # Diagnostic Alert Badge
            alert_bg = hex_to_rgb(self.colors.get("badge_bg", "#3b1111"))
            alert_text_col = hex_to_rgb(self.colors.get("accent_secondary", "#f87171"))
            alert_str = "● FORENSIC SURVEILLANCE // INGESTION GATE ACTIVE"
            ab = draw.textbbox((inner_x, inner_y), alert_str, font=self.font_badge)
            draw.rectangle([inner_x - 10, inner_y - 6, ab[2] + 10, ab[3] + 6], fill=alert_bg, outline=alert_text_col, width=1)
            draw.text((inner_x, inner_y), alert_str, fill=alert_text_col, font=self.font_badge)
            inner_y = ab[3] + 44

            # Main Title (Monospace High Impact)
            head_lines = wrap_text(headline, self.font_title, inner_w, draw)
            for line in head_lines:
                draw.text((inner_x, inner_y), line, fill=foreground_color, font=self.font_title)
                tb = draw.textbbox((inner_x, inner_y), line, font=self.font_title)
                inner_y = tb[3] + self.line_spacing + 4

            # Hairline divider
            inner_y += 24
            draw.line([(inner_x, inner_y), (inner_x + inner_w, inner_y)], fill=card_border, width=1)
            inner_y += 28

            # Subtitle
            if supporting_text:
                sub_lines = wrap_text(supporting_text, self.font_subtitle, inner_w, draw)
                for line in sub_lines:
                    draw.text((inner_x, inner_y), line, fill=secondary_color, font=self.font_subtitle)
                    tb = draw.textbbox((inner_x, inner_y), line, font=self.font_subtitle)
                    inner_y = tb[3] + self.line_spacing

            # Bottom diagnostic telemetry readout
            foot_y = card_y1 - 60
            draw.line([(card_x0 + 20, foot_y - 12), (card_x1 - 20, foot_y - 12)], fill=card_border, width=1)
            diagnostic_str = "GATE://STREAM-01 • SCAN_ID: #4092 • DEFECT: ISOLATED • LEAK: 0%"
            draw.text((inner_x, foot_y), diagnostic_str, fill=hex_to_rgb(self.colors.get("muted", "#484f58")), font=self.font_caption)

        elif header_style == "cinematic_hud":
            # Cinematic Data Viz aesthetic: Sleek, deep canvas with luminous glow and expansive air
            card_w = self.width - 2 * self.pad_x
            avail_h = self.height - 2 * self.pad_y
            card_h = min(avail_h, 1080)
            card_x0 = self.pad_x
            card_y0 = self.pad_y + (avail_h - card_h) // 2
            card_x1 = card_x0 + card_w
            card_y1 = card_y0 + card_h

            # Floating glassmorphic card with subtle thin border
            draw.rounded_rectangle(
                [card_x0, card_y0, card_x1, card_y1],
                radius=self.border_radius,
                fill=card_bg,
                outline=card_border,
                width=1
            )

            inner_x = card_x0 + self.card_pad + 24
            inner_y = card_y0 + 100
            inner_w = card_w - 2 * (self.card_pad + 24)

            # Luminous status pill
            pill_text = tag.upper() if tag else "TELEMETRY SURVEILLANCE // INGESTION"
            tb = draw.textbbox((inner_x, inner_y), pill_text, font=self.font_badge)
            pill_r = 16
            draw.rounded_rectangle(
                [inner_x - 14, inner_y - 8, tb[2] + 28, tb[3] + 8],
                radius=pill_r,
                fill=hex_to_rgb(self.colors.get("badge_bg", "#0f2238")),
                outline=accent_color,
                width=1
            )
            # Glowing accent dot inside pill
            dot_cx = inner_x + 2
            dot_cy = (inner_y - 8 + tb[3] + 8) // 2
            draw.ellipse([dot_cx - 4, dot_cy - 4, dot_cx + 4, dot_cy + 4], fill=accent_color)
            draw.text((inner_x + 16, inner_y), pill_text, fill=foreground_color, font=self.font_badge)
            inner_y = tb[3] + 56

            # Main Cinematic Headline
            head_lines = wrap_text(headline, self.font_title, inner_w, draw)
            for line in head_lines:
                draw.text((inner_x, inner_y), line, fill=foreground_color, font=self.font_title)
                tb = draw.textbbox((inner_x, inner_y), line, font=self.font_title)
                inner_y = tb[3] + self.line_spacing + 6

            # Luminous gradient divider
            inner_y += 24
            draw.line([(inner_x, inner_y), (inner_x + 180, inner_y)], fill=accent_color, width=4)
            draw.line([(inner_x + 180, inner_y), (inner_x + inner_w, inner_y)], fill=card_border, width=1)
            inner_y += 36

            # Supporting deck
            if supporting_text:
                sub_lines = wrap_text(supporting_text, self.font_subtitle, inner_w, draw)
                for line in sub_lines:
                    draw.text((inner_x, inner_y), line, fill=secondary_color, font=self.font_subtitle)
                    tb = draw.textbbox((inner_x, inner_y), line, font=self.font_subtitle)
                    inner_y = tb[3] + self.line_spacing + 2

            # Bottom cinematic metric callout bar
            bar_y = card_y1 - 100
            metric_pill_w = inner_w
            draw.rounded_rectangle(
                [inner_x, bar_y, inner_x + metric_pill_w, bar_y + 54],
                radius=8,
                fill=hex_to_rgb(self.colors.get("code_bg", "#08101e")),
                outline=card_border,
                width=1
            )
            draw.text(
                (inner_x + 20, bar_y + 16),
                "● STREAM INTEGRITY: 100% • 1 DEFECT CONTAINED • 0 DOWNSTREAM LEAKS",
                fill=accent_color,
                font=self.font_badge
            )

        else:
            # Editorial aesthetic: Prestigious publication masthead & cover layout
            max_w = self.width - 2 * self.pad_x
            curr_y = self.pad_y + 20

            # Top masthead eyebrow
            tag_text = tag.upper() if tag else "TOPIC VIDEO REPORT // BRIEFING"
            draw.text((self.pad_x, curr_y), tag_text, fill=accent_color, font=self.font_badge)

            edition_marker = "TOPIC VIDEO ENGINE • EDITION 01"
            eb = draw.textbbox((0, 0), edition_marker, font=self.font_caption)
            draw.text(
                (self.width - self.pad_x - (eb[2] - eb[0]), curr_y - 2),
                edition_marker,
                fill=secondary_color,
                font=self.font_caption,
            )

            tb = draw.textbbox((self.pad_x, curr_y), tag_text, font=self.font_badge)
            curr_y = tb[3] + 16

            # Heavy publication rule
            draw.line([(self.pad_x, curr_y), (self.width - self.pad_x, curr_y)], fill=foreground_color, width=4)
            curr_y += 60

            # Editorial hero layout - vertically centered between masthead and footer
            top_rule_y = curr_y
            bottom_rule_y = self.height - self.pad_y - 20

            serif_families = self.typography.get("font_families", ["Georgia", "Times New Roman"])
            font_hero = get_font(serif_families, 72)
            head_lines = wrap_text(headline, font_hero, max_w, draw)
            sub_lines = wrap_text(supporting_text, self.font_subtitle, max_w, draw) if supporting_text else []

            # Calculate total hero height
            head_h = len(head_lines) * (draw.textbbox((0, 0), "A", font=font_hero)[3] + self.line_spacing + 10)
            sub_h = len(sub_lines) * (draw.textbbox((0, 0), "A", font=self.font_subtitle)[3] + self.line_spacing + 4) if sub_lines else 0
            hero_h = head_h + 24 + 5 + 36 + sub_h

            avail_h = bottom_rule_y - top_rule_y
            curr_y = top_rule_y + max(40, (avail_h - hero_h) // 2)

            # Draw Headline
            for line in head_lines:
                draw.text((self.pad_x, curr_y), line, fill=foreground_color, font=font_hero)
                tb = draw.textbbox((self.pad_x, curr_y), line, font=font_hero)
                curr_y = tb[3] + self.line_spacing + 10

            # Crimson editorial accent divider
            curr_y += 20
            draw.line([(self.pad_x, curr_y), (self.pad_x + 180, curr_y)], fill=accent_color, width=5)
            curr_y += 36

            # Supporting deck
            for line in sub_lines:
                draw.text((self.pad_x, curr_y), line, fill=secondary_color, font=self.font_subtitle)
                tb = draw.textbbox((self.pad_x, curr_y), line, font=self.font_subtitle)
                curr_y = tb[3] + self.line_spacing + 4

            # Bottom editorial decorative footer rule
            draw.line([(self.pad_x, bottom_rule_y), (self.width - self.pad_x, bottom_rule_y)], fill=hex_to_rgb(self.colors.get("card_border", "#e7e5e4")), width=1)
            draw.text(
                (self.pad_x, bottom_rule_y + 12),
                "RESEARCH BRIEFING • AUTONOMOUS VIDEO SLICE",
                fill=hex_to_rgb(self.colors.get("muted", "#a8a29e")),
                font=self.font_caption,
            )

        if scene_data.get("personal_signature"):
            sig_y = self.height - max(self.pad_y, getattr(self, "safe_bottom", 160)) - 70
            self.draw_personal_signature(draw, scene_data["personal_signature"], y_pos=sig_y)

        if footnote:
            self.draw_footnote(draw, footnote)

        return img
