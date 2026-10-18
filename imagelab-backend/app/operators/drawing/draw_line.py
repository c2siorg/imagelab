import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_draw_color


class DrawLine(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        result = image.copy()
        thickness = max(1, int(self.params.get("thickness", 2)))
        color = hex_to_draw_color(self.params.get("rgbcolors_input", "#2828cc"), result)
        x1 = int(self.params.get("starting_point_x1", 0))
        y1 = int(self.params.get("starting_point_y1", 0))
        x2 = int(self.params.get("ending_point_x", 0))
        y2 = int(self.params.get("ending_point_y", 0))
        cv2.line(result, (x1, y1), (x2, y2), color, thickness)
        return result
