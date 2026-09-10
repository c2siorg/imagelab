import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


class DrawText(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        result = image.copy()
        text = str(self.params.get("draw_text", "Image Lab"))
        thickness = max(1, int(self.params.get("thickness", 2)))
        scale = max(0.1, float(self.params.get("scale", 1)))
        color = hex_to_bgr(self.params.get("rgbcolors_input", "#2828cc"))
        x = int(self.params.get("starting_point_x", 0))

        font = cv2.FONT_HERSHEY_SIMPLEX
        (_, text_height), baseline = cv2.getTextSize(text, font, scale, thickness)
        default_y = text_height + baseline
        y = int(self.params.get("starting_point_y", default_y))

        cv2.putText(result, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)
        return result
