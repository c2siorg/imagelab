import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_draw_color


class DrawLine(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 2 or (image.ndim == 3 and image.shape[2] == 1):
            image = cv2.cvtColor(image if image.ndim == 2 else image[:, :, 0], cv2.COLOR_GRAY2BGR)
        result = image.copy()
        try:
            thickness_val = int(self.params.get("thickness", 2))
        except (TypeError, ValueError):
            thickness_val = 2
        thickness = max(1, thickness_val)
        color = hex_to_draw_color(self.params.get("rgbcolors_input", "#2828cc"), result)
        x1_raw = self.params.get("starting_point_x1")
        if x1_raw is None:
            x1_raw = self.params.get("starting_point_x", 0)
        y1_raw = self.params.get("starting_point_y1")
        if y1_raw is None:
            y1_raw = self.params.get("starting_point_y", 0)
        try:
            x1 = int(x1_raw)
        except (TypeError, ValueError):
            x1 = 0
        try:
            y1 = int(y1_raw)
        except (TypeError, ValueError):
            y1 = 0
        try:
            x2 = int(self.params.get("ending_point_x", 0))
        except (TypeError, ValueError):
            x2 = 0
        try:
            y2 = int(self.params.get("ending_point_y", 0))
        except (TypeError, ValueError):
            y2 = 0
        cv2.line(result, (x1, y1), (x2, y2), color, thickness)
        return result
