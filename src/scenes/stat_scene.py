"""Stat callout / Key metric scene renderer."""

from typing import Any, Dict
from PIL import Image

from src.scenes.base import BaseScene, hex_to_rgb, wrap_text
from src.scenes.fonts import get_font


class StatScene(BaseScene):
    """Renders prominent numerical highlights and stat callouts."""

    def render(self, scene_data: Dict[str, Any]) -> Image.Image:
        img, draw = self.create_canvas()

        headline = scene_data.get("headline", "")
        stat_value = scene_data.get("stat_value", "")
        stat_label = scene_data.get("stat_label", "")
        supporting_text = scene_data.get("supporting_text", "")
        tag = scene_data.get("tag", "")
        footnote = scene_data.get("footnote", "")

        content_y = self.draw_header(draw, headline, tag=tag)

        stat_cfg = self.components.get("stat", {})
        if scene_data.get("semantic"):
            num_color = self.get_semantic_color(scene_data["semantic"])
        else:
            num_color = hex_to_rgb(stat_cfg.get("number_color", "#b91c1c"))

        lbl_color = hex_to_rgb(stat_cfg.get("label_color", "#1c1917"))
        sec_color = hex_to_rgb(self.colors.get("secondary", "#57534e"))
        card_bg = hex_to_rgb(self.colors.get("card_bg", "#ffffff"))
        card_border = hex_to_rgb(self.colors.get("card_border", "#e7e5e4"))
        accent_color = hex_to_rgb(self.colors.get("accent", "#b91c1c"))

        card_x0 = self.pad_x
        card_y0 = content_y + 10
        card_w = self.width - 2 * self.pad_x
        has_sig = bool(scene_data.get("personal_signature"))
        bottom_space = 140 if has_sig else (80 if footnote else 40)
        max_card_h = self.height - self.pad_y - bottom_space - card_y0

        inner_x = card_x0 + self.card_pad + 20
        inner_w = card_w - 2 * (self.card_pad + 20)

        # Pre-calculate content height to size card appropriately
        font_stat_hero = get_font(self.typography.get("font_families", ["Georgia"]), 96)
        stat_h = 110 if stat_value else 0
        lbl_lines = wrap_text(stat_label, self.font_headline, inner_w, draw) if stat_label else []
        lbl_h = len(lbl_lines) * 54
        sub_lines = wrap_text(supporting_text, self.font_subtitle, inner_w - 60, draw) if supporting_text else []
        box_h = len(sub_lines) * 44 + 50 if sub_lines else 0

        needed_h = self.card_pad * 2 + stat_h + 30 + lbl_h + 36 + box_h + 20
        card_h = min(max_card_h, max(520, needed_h))
        card_y1 = card_y0 + card_h

        # Draw Card container
        draw.rounded_rectangle(
            [card_x0, card_y0, card_x0 + card_w, card_y1],
            radius=self.border_radius,
            fill=card_bg,
            outline=card_border,
            width=2
        )

        curr_inner_y = card_y0 + self.card_pad + 10

        # Stat value (Giant number/metric)
        if stat_value:
            draw.text((inner_x, curr_inner_y), stat_value, fill=num_color, font=font_stat_hero)
            vb = draw.textbbox((inner_x, curr_inner_y), stat_value, font=font_stat_hero)
            curr_inner_y = vb[3] + 16

        # Accent underline
        draw.line([(inner_x, curr_inner_y), (inner_x + 160, curr_inner_y)], fill=accent_color, width=5)
        curr_inner_y += 32

        # Stat label
        for line in lbl_lines:
            draw.text((inner_x, curr_inner_y), line, fill=lbl_color, font=self.font_headline)
            tb = draw.textbbox((inner_x, curr_inner_y), line, font=self.font_headline)
            curr_inner_y = tb[3] + self.line_spacing + 2

        # Supporting text callout block
        if sub_lines:
            curr_inner_y += 28
            box_x0 = inner_x
            box_y0 = curr_inner_y
            box_w = inner_w

            code_bg = hex_to_rgb(self.colors.get("code_bg", "#f5f5f4"))
            draw.rounded_rectangle(
                [box_x0, box_y0, box_x0 + box_w, box_y0 + box_h],
                radius=4,
                fill=code_bg
            )
            # Left accent highlight bar
            draw.rectangle(
                [box_x0, box_y0, box_x0 + 6, box_y0 + box_h],
                fill=accent_color
            )

            text_y = box_y0 + 20
            for sl in sub_lines:
                draw.text((box_x0 + 26, text_y), sl, fill=sec_color, font=self.font_subtitle)
                sb = draw.textbbox((box_x0 + 26, text_y), sl, font=self.font_subtitle)
                text_y = sb[3] + self.line_spacing

        if scene_data.get("personal_signature"):
            sig_y = card_y1 + 18
            self.draw_personal_signature(draw, scene_data["personal_signature"], y_pos=sig_y)

        if footnote:
            self.draw_footnote(draw, footnote)

        return img
