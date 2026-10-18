"""Data chart scene renderer optimized for 9:16 vertical and horizontal canvases."""

from typing import Any, Dict
from PIL import Image

from src.scenes.base import BaseScene, hex_to_rgb


class ChartScene(BaseScene):
    """Renders data visualization charts with mobile-first stacked bar layout."""

    def render(self, scene_data: Dict[str, Any]) -> Image.Image:
        img, draw = self.create_canvas()

        headline = scene_data.get("headline", "")
        supporting_text = scene_data.get("supporting_text", "")
        tag = scene_data.get("tag", "")
        footnote = scene_data.get("footnote", "")
        data_points = scene_data.get("data_points", [])

        content_y = self.draw_header(draw, headline, tag=tag, supporting_text=supporting_text)

        chart_cfg = self.components.get("chart", {})
        bar_color = hex_to_rgb(chart_cfg.get("bar_color", "#38bdf8"))
        bar_highlight_color = hex_to_rgb(chart_cfg.get("bar_color_highlight", "#34d399"))
        bar_bg_color = hex_to_rgb(chart_cfg.get("bar_bg", "#21262d"))
        bar_radius = chart_cfg.get("bar_radius", 4)
        label_color = hex_to_rgb(chart_cfg.get("label_color", "#e6edf3"))
        value_color = hex_to_rgb(chart_cfg.get("value_color", "#38bdf8"))
        card_bg = hex_to_rgb(self.colors.get("card_bg", "#161b22"))
        card_border = hex_to_rgb(self.colors.get("card_border", "#30363d"))

        card_x0 = self.pad_x
        card_y0 = content_y + 10
        card_w = self.width - 2 * self.pad_x
        has_sig = bool(scene_data.get("personal_signature"))
        bottom_space = 140 if has_sig else (80 if footnote else 40)
        max_card_h = self.height - self.pad_y - bottom_space - card_y0

        total_items = max(len(data_points), 1)
        row_height = 135
        needed_card_h = total_items * row_height + 2 * self.card_pad
        card_h = min(max_card_h, max(460, needed_card_h))
        card_y1 = card_y0 + card_h

        draw.rounded_rectangle(
            [card_x0, card_y0, card_x0 + card_w, card_y1],
            radius=self.border_radius,
            fill=card_bg,
            outline=card_border,
            width=2
        )

        if data_points:
            inner_x = card_x0 + self.card_pad + 10
            inner_w = card_w - 2 * (self.card_pad + 10)

            # Distribute rows evenly across card
            avail_rows_h = card_h - 2 * self.card_pad
            row_h = avail_rows_h / total_items
            start_y = card_y0 + self.card_pad

            max_abs = max(abs(float(p.get("value", 0))) for p in data_points) or 1.0

            for i, dp in enumerate(data_points):
                curr_row_y = start_y + i * row_h
                label = str(dp.get("label", ""))
                val = float(dp.get("value", 0))
                unit = str(dp.get("unit", ""))

                # Point-specific styling
                is_highlighted = dp.get("highlight", False) or (i == 0 and "highlight" not in dp)
                if dp.get("color"):
                    item_col = hex_to_rgb(dp["color"])
                elif dp.get("semantic"):
                    item_col = self.get_semantic_color(dp["semantic"])
                elif is_highlighted:
                    item_col = bar_highlight_color
                else:
                    item_col = bar_color

                val_col = item_col if is_highlighted or dp.get("color") else value_color

                # Label on left
                draw.text((inner_x, curr_row_y), label, fill=label_color, font=self.font_body)

                # Optional status badge next to label
                status_tag = dp.get("status")
                if status_tag:
                    lb = draw.textbbox((inner_x, curr_row_y), label, font=self.font_body)
                    badge_x = lb[2] + 16
                    sb = draw.textbbox((badge_x, curr_row_y + 2), status_tag, font=self.font_badge)
                    draw.rounded_rectangle(
                        [badge_x - 6, curr_row_y + 1, sb[2] + 6, sb[3] + 3],
                        radius=3,
                        fill=hex_to_rgb(self.colors.get("badge_bg", "#1f2937")),
                        outline=item_col,
                        width=1
                    )
                    draw.text((badge_x, curr_row_y + 2), status_tag, fill=item_col, font=self.font_badge)

                # Value formatted on right
                val_text = dp.get("formatted_value") or f"{int(val) if val.is_integer() else val}{unit}"
                vb = draw.textbbox((0, 0), val_text, font=self.font_body)
                val_w = vb[2] - vb[0]
                val_x = inner_x + inner_w - val_w
                draw.text((val_x, curr_row_y), val_text, fill=val_col, font=self.font_body)

                # Bar track underneath label line
                bar_y0 = curr_row_y + 36
                bar_h_px = 32
                bar_y1 = bar_y0 + bar_h_px
                draw.rounded_rectangle(
                    [inner_x, bar_y0, inner_x + inner_w, bar_y1],
                    radius=bar_radius,
                    fill=bar_bg_color
                )

                # Filled bar
                ratio = min(max(abs(val) / max_abs, 0.0), 1.0)
                fill_w = max(int(inner_w * ratio), 8)
                draw.rounded_rectangle(
                    [inner_x, bar_y0, inner_x + fill_w, bar_y1],
                    radius=bar_radius,
                    fill=item_col
                )

                # Hairline row divider except last item
                if i < total_items - 1:
                    div_y = curr_row_y + row_h - 10
                    draw.line([(inner_x, div_y), (inner_x + inner_w, div_y)], fill=card_border, width=1)

        if scene_data.get("personal_signature"):
            sig_y = card_y1 + 18
            self.draw_personal_signature(draw, scene_data["personal_signature"], y_pos=sig_y)

        if footnote:
            self.draw_footnote(draw, footnote)

        return img
