import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


class DrawLine(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        result = image.copy()
        thickness = int(self.params.get("thickness", 2))
        color = hex_to_bgr(self.params.get("rgbcolors_input", "#2828cc"))
        x1 = int(self.params.get("starting_point_x1", 0))
        y1 = int(self.params.get("starting_point_y1", 0))
        x2 = int(self.params.get("ending_point_x", 0))
        y2 = int(self.params.get("ending_point_y", 0))
        cv2.line(result, (x1, y1), (x2, y2), color, thickness)
        return result
