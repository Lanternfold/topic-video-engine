"""Terminal / Command workflow scene renderer."""

from typing import Any, Dict
from PIL import Image

from src.scenes.base import BaseScene, hex_to_rgb


class TerminalScene(BaseScene):
    """Renders command-line executions, logs, and code workflow demonstrations."""

    def render(self, scene_data: Dict[str, Any]) -> Image.Image:
        img, draw = self.create_canvas()

        headline = scene_data.get("headline", "")
        supporting_text = scene_data.get("supporting_text", "")
        tag = scene_data.get("tag", "")
        footnote = scene_data.get("footnote", "")
        term_data = scene_data.get("terminal", {})

        command = term_data.get("command", "")
        output_lines = term_data.get("output", [])

        # Draw standard header
        content_y = self.draw_header(draw, headline, tag=tag, supporting_text=supporting_text)

        # Terminal card geometry
        term_cfg = self.components.get("terminal", {})
        show_dots = term_cfg.get("show_window_dots", True)
        window_title = term_cfg.get("window_title", "terminal")
        prompt_sym = term_cfg.get("prompt_symbol", "$")

        card_x0 = self.pad_x
        card_y0 = content_y + 10
        card_w = self.width - 2 * self.pad_x
        has_sig = bool(scene_data.get("personal_signature"))
        bottom_space = 140 if has_sig else (80 if footnote else 40)
        max_card_h = self.height - self.pad_y - bottom_space - card_y0

        card_bg = hex_to_rgb(self.colors.get("code_bg", "#0b0f14"))
        card_border = hex_to_rgb(self.colors.get("card_border", "#30363d"))
        bar_bg = hex_to_rgb(self.colors.get("card_bg", "#161b22"))
        prompt_color = hex_to_rgb(term_cfg.get("prompt_color", "#38bdf8"))
        command_color = hex_to_rgb(term_cfg.get("command_color", "#f0f6fc"))
        output_color = hex_to_rgb(term_cfg.get("output_color", "#8b949e"))
        secondary_color = hex_to_rgb(self.colors.get("secondary", "#8b949e"))

        # Calculate needed height
        bar_h = 46
        cmd_h = 60 if command else 0
        out_h = len(output_lines) * 44
        status_h = 48 if show_dots else 0
        needed_h = bar_h + 30 + cmd_h + out_h + status_h + 40
        card_h = min(max_card_h, max(460, needed_h))
        card_y1 = card_y0 + card_h

        # Outer card
        draw.rounded_rectangle(
            [card_x0, card_y0, card_x0 + card_w, card_y1],
            radius=self.border_radius,
            fill=card_bg,
            outline=card_border,
            width=2
        )

        # Title bar
        draw.rounded_rectangle(
            [card_x0, card_y0, card_x0 + card_w, card_y0 + bar_h],
            radius=self.border_radius,
            fill=bar_bg
        )
        draw.rectangle(
            [card_x0, card_y0 + bar_h - 10, card_x0 + card_w, card_y0 + bar_h],
            fill=bar_bg
        )
        draw.line(
            [(card_x0, card_y0 + bar_h), (card_x0 + card_w, card_y0 + bar_h)],
            fill=card_border,
            width=1
        )

        dot_y = card_y0 + bar_h // 2
        title_start_x = card_x0 + 20
        if show_dots:
            dot_colors = [(239, 68, 68), (234, 179, 8), (34, 197, 94)]
            for i, col in enumerate(dot_colors):
                cx = card_x0 + 22 + i * 18
                draw.ellipse([cx - 5, dot_y - 5, cx + 5, dot_y + 5], fill=col)
            title_start_x = card_x0 + 90

        draw.text((title_start_x, dot_y - 9), window_title, fill=secondary_color, font=self.font_caption)

        # Code & Output contents
        line_x = card_x0 + self.card_pad + 10
        line_y = card_y0 + bar_h + 30

        # Command line with prompt
        if command:
            draw.text((line_x, line_y), f"{prompt_sym} ", fill=prompt_color, font=self.font_code)
            pb = draw.textbbox((line_x, line_y), f"{prompt_sym} ", font=self.font_code)
            draw.text((pb[2], line_y), command, fill=command_color, font=self.font_code)
            tb = draw.textbbox((line_x, line_y), f"{prompt_sym} {command}", font=self.font_code)
            line_y = tb[3] + 20

            # Subtle separator between command and output
            draw.line([(line_x, line_y), (card_x0 + card_w - (self.card_pad + 10), line_y)], fill=card_border, width=1)
            line_y += 24

        # Output lines
        error_color = hex_to_rgb(term_cfg.get("error_color", "#f87171"))
        warning_color = hex_to_rgb(term_cfg.get("warning_color", "#fbbf24"))
        for out in output_lines:
            stripped = out.strip().upper()
            if stripped.startswith(("✓", "✔", "SUCCESS", "PASS")):
                col = hex_to_rgb(term_cfg.get("success_color", "#34d399"))
            elif stripped.startswith(("✗", "FAIL", "ERROR", "ALERT", "QUARANTINED", "VIOLATION", "[ALERT]", "[FAIL]", "[QUARANTINED]")):
                col = error_color
            elif stripped.startswith(("WARN", "WARNING", "[WARN]")):
                col = warning_color
            else:
                col = output_color

            draw.text((line_x, line_y), out, fill=col, font=self.font_code)
            tb = draw.textbbox((line_x, line_y), out, font=self.font_code)
            line_y = tb[3] + 16

        # Bottom terminal status line
        status_text = term_data.get("status_line") or term_cfg.get("status_line")
        if status_text or show_dots:
            if not status_text:
                status_text = "STATUS: EXITED (0) • DURATION: 14.2s • RUNNERS: 4/4 ACTIVE"
            status_y = card_y1 - 36
            draw.line([(card_x0, status_y), (card_x0 + card_w, status_y)], fill=card_border, width=1)
            draw.text(
                (line_x, status_y + 8),
                status_text,
                fill=secondary_color,
                font=self.font_caption
            )

        if scene_data.get("personal_signature"):
            sig_y = card_y1 + 18
            self.draw_personal_signature(draw, scene_data["personal_signature"], y_pos=sig_y)

        if footnote:
            self.draw_footnote(draw, footnote)

        return img
