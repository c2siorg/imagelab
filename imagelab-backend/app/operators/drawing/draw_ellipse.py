import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_draw_color


class DrawEllipse(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        result = image.copy()
        try:
            thickness_val = int(self.params.get("thickness", 2))
        except (TypeError, ValueError):
            thickness_val = 2
        thickness = -1 if thickness_val == -1 else max(1, thickness_val)

        try:
            height = max(0, int(self.params.get("height", 0)))
        except (TypeError, ValueError):
            height = 0

        try:
            width = max(0, int(self.params.get("width", 0)))
        except (TypeError, ValueError):
            width = 0

        try:
            angle = int(self.params.get("angle", 0))
        except (TypeError, ValueError):
            angle = 0

        color = hex_to_draw_color(self.params.get("rgbcolors_input", "#2828cc"), result)

        try:
            cx = int(self.params.get("center_point_x", 0))
        except (TypeError, ValueError):
            cx = 0

        try:
            cy = int(self.params.get("center_point_y", 0))
        except (TypeError, ValueError):
            cy = 0

        cv2.ellipse(result, (cx, cy), (width, height), angle, 0, 360, color, thickness)
        return result
