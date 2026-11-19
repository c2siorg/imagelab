import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_draw_color


class DrawText(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 2 or (image.ndim == 3 and image.shape[2] == 1):
            image = cv2.cvtColor(image if image.ndim == 2 else image[:, :, 0], cv2.COLOR_GRAY2BGR)
        result = image.copy()
        text = str(self.params.get("draw_text", "Image Lab"))
        try:
            thickness_val = int(self.params.get("thickness", 2))
        except (TypeError, ValueError):
            thickness_val = 2
        thickness = max(1, thickness_val)
        try:
            scale_val = float(self.params.get("scale", 1))
        except (TypeError, ValueError):
            scale_val = 1.0
        scale = max(0.1, scale_val)
        color = hex_to_draw_color(self.params.get("rgbcolors_input", "#2828cc"), result)
        try:
            x = int(self.params.get("starting_point_x", 0))
        except (TypeError, ValueError):
            x = 0

        font = cv2.FONT_HERSHEY_SIMPLEX
        (_, text_height), baseline = cv2.getTextSize(text, font, scale, thickness)
        default_y = text_height + baseline
        try:
            y = int(self.params.get("starting_point_y", default_y))
        except (TypeError, ValueError):
            y = default_y

        cv2.putText(result, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)
        return result
