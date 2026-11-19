import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_draw_color


class DrawCircle(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 2 or (image.ndim == 3 and image.shape[2] == 1):
            image = cv2.cvtColor(image if image.ndim == 2 else image[:, :, 0], cv2.COLOR_GRAY2BGR)
        result = image.copy()
        try:
            thickness_val = int(self.params.get("thickness", 2))
        except (TypeError, ValueError):
            thickness_val = 2
        thickness = -1 if thickness_val == -1 else max(1, thickness_val)
        try:
            radius = max(0, int(self.params.get("radius", 5)))
        except (TypeError, ValueError):
            radius = 5
        color = hex_to_draw_color(self.params.get("rgbcolors_input", "#2828cc"), result)
        try:
            cx = int(self.params.get("center_point_x", 0))
        except (TypeError, ValueError):
            cx = 0
        try:
            cy = int(self.params.get("center_point_y", 0))
        except (TypeError, ValueError):
            cy = 0
        cv2.circle(result, (cx, cy), radius, color, thickness)
        return result
