import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_draw_color


class DrawCircle(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        result = image.copy()
        thickness = int(self.params.get("thickness", 2))
        radius = max(0, int(self.params.get("radius", 5)))
        color = hex_to_draw_color(self.params.get("rgbcolors_input", "#2828cc"), result)
        cx = int(self.params.get("center_point_x", 0))
        cy = int(self.params.get("center_point_y", 0))
        cv2.circle(result, (cx, cy), radius, color, thickness)
        return result
