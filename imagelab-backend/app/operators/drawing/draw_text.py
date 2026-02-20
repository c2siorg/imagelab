import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


class DrawText(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        result = image.copy()
        text = str(self.params.get("draw_text", "Image Lab"))
        thickness = int(self.params.get("thickness", 2))
        scale = float(self.params.get("scale", 1))
        color = hex_to_bgr(self.params.get("rgbcolors_input", "#2828cc"))
        x = int(self.params.get("starting_point_x", 0))
        y = int(self.params.get("starting_point_y", 0))
        cv2.putText(result, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)
        return result
