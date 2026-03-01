import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


class ContourDetection(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        mode_str = str(self.params.get("mode", "EXTERNAL")).upper()
        method_str = str(self.params.get("method", "SIMPLE")).upper()
        thickness = int(self.params.get("thickness", 2))
        hex_color = self.params.get("rgbcolors_input", "#00ff00")
        bgr_color = hex_to_bgr(hex_color)

        mode = cv2.RETR_TREE if mode_str == "TREE" else cv2.RETR_EXTERNAL
        method = cv2.CHAIN_APPROX_NONE if method_str == "NONE" else cv2.CHAIN_APPROX_SIMPLE

        # Convert to single-channel 8-bit image for findContours
        if image.ndim == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif image.ndim == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        else:
            gray = image.copy()

        if gray.dtype != np.uint8:
            gray = gray.astype(np.uint8)

        # Do not bake in opinionated thresholding/blur here.
        # findContours expects a binary mask or single-channel image directly.
        # Standard OpenCV behavior: non-zero pixels are treated as 1 (foreground).
        ret = cv2.findContours(gray, mode, method)
        contours = ret[-2]

        if not contours:
            return image

        result = image.copy()

        # Format the color properly for the output channels to prevent crashes
        if result.ndim == 2:
            result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
            draw_color = bgr_color
        elif result.ndim == 3 and result.shape[2] == 4:
            # For BGRA images, OpenCV drawContours supports 4-tuple colors
            draw_color = (*bgr_color, 255)
        else:
            draw_color = bgr_color

        cv2.drawContours(result, contours, -1, draw_color, thickness)

        return result
