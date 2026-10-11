"""Conclusion / Summary takeaways scene renderer."""

from typing import Any, Dict
from PIL import Image

from src.scenes.base import BaseScene, hex_to_rgb, wrap_text
from src.scenes.fonts import get_font


class ConclusionScene(BaseScene):
    """Renders closing summary cards and key takeaway lists."""

    def render(self, scene_data: Dict[str, Any]) -> Image.Image:
        img, draw = self.create_canvas()

        headline = scene_data.get("headline", "")
        supporting_text = scene_data.get("supporting_text", "")
        tag = scene_data.get("tag", "")
        footnote = scene_data.get("footnote", "")
        bullet_points = scene_data.get("bullet_points", [])

        content_y = self.draw_header(draw, headline, tag=tag, supporting_text=supporting_text)

        header_style = self.layout.get("header_style", "terminal_dots")
        accent_color = hex_to_rgb(self.colors.get("accent", "#38bdf8"))
        foreground_color = hex_to_rgb(self.colors.get("foreground", "#e6edf3"))
        card_bg = hex_to_rgb(self.colors.get("card_bg", "#161b22"))
        card_border = hex_to_rgb(self.colors.get("card_border", "#30363d"))
        success_color = hex_to_rgb(self.components.get("terminal", {}).get("success_color", "#34d399"))

        card_x0 = self.pad_x
        card_y0 = content_y + 10
        card_w = self.width - 2 * self.pad_x
        bottom_space = 80 if footnote else 40
        max_card_h = self.height - self.pad_y - bottom_space - card_y0

        total_items = max(len(bullet_points), 1)
        needed_card_h = total_items * 130 + 2 * self.card_pad
        card_h = min(max_card_h, max(460, needed_card_h))
        card_y1 = card_y0 + card_h

        draw.rounded_rectangle(
            [card_x0, card_y0, card_x0 + card_w, card_y1],
            radius=self.border_radius,
            fill=card_bg,
            outline=card_border,
            width=2
        )

        inner_x = card_x0 + self.card_pad + 20
        inner_w = card_w - 2 * (self.card_pad + 20)

        avail_h = card_h - 2 * self.card_pad
        item_h = avail_h / total_items
        start_y = card_y0 + self.card_pad

        for i, point in enumerate(bullet_points):
            row_y = start_y + i * item_h

            if header_style == "terminal_dots":
                # Developer workflow style: Checkmark + index badge + text
                bullet_prefix = "✓"
                badge_str = f"0{i+1}"

                draw.rounded_rectangle(
                    [inner_x, row_y + 4, inner_x + 48, row_y + 36],
                    radius=4,
                    fill=hex_to_rgb(self.colors.get("code_bg", "#0b0f14")),
                    outline=card_border,
                    width=1
                )
                draw.text((inner_x + 12, row_y + 8), badge_str, fill=accent_color, font=self.font_caption)
                draw.text((inner_x + 64, row_y + 6), bullet_prefix, fill=success_color, font=self.font_subtitle)

                text_start_x = inner_x + 100
                text_max_w = inner_w - 100
                lines = wrap_text(point, self.font_subtitle, text_max_w, draw)
                curr_text_y = row_y + 6
                for line in lines:
                    draw.text((text_start_x, curr_text_y), line, fill=foreground_color, font=self.font_subtitle)
                    tb = draw.textbbox((text_start_x, curr_text_y), line, font=self.font_subtitle)
                    curr_text_y = tb[3] + 6

                if i < len(bullet_points) - 1:
                    div_y = row_y + item_h - 10
                    draw.line([(inner_x, div_y), (inner_x + inner_w, div_y)], fill=card_border, width=1)

            else:
                # Editorial style: Numbered section (01, 02, 03)
                num_label = f"0{i+1}"
                font_num = get_font(self.typography.get("font_families", ["Georgia"]), 36)
                draw.text((inner_x, row_y + 4), num_label, fill=accent_color, font=font_num)

                text_start_x = inner_x + 75
                text_max_w = inner_w - 75

                lines = wrap_text(point, self.font_subtitle, text_max_w, draw)
                curr_text_y = row_y + 6
                for line in lines:
                    draw.text((text_start_x, curr_text_y), line, fill=foreground_color, font=self.font_subtitle)
                    tb = draw.textbbox((text_start_x, curr_text_y), line, font=self.font_subtitle)
                    curr_text_y = tb[3] + 6

                if i < len(bullet_points) - 1:
                    div_y = row_y + item_h - 10
                    draw.line([(inner_x, div_y), (inner_x + inner_w, div_y)], fill=card_border, width=1)

        if footnote:
            self.draw_footnote(draw, footnote)

        return img
