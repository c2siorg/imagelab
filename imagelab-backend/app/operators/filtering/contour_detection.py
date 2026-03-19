import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr

_MODE_MAP = {"EXTERNAL": cv2.RETR_EXTERNAL, "TREE": cv2.RETR_TREE}
_METHOD_MAP = {"SIMPLE": cv2.CHAIN_APPROX_SIMPLE, "NONE": cv2.CHAIN_APPROX_NONE}


class ContourDetection(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        mode_str = str(self.params.get("mode", "EXTERNAL")).upper()
        method_str = str(self.params.get("method", "SIMPLE")).upper()
        thickness = int(self.params.get("thickness", 2))
        bgr_color = hex_to_bgr(self.params.get("rgbcolors_input", "#00ff00"))

        if mode_str not in _MODE_MAP:
            raise ValueError(f"Invalid contour mode '{mode_str}'. Must be one of {list(_MODE_MAP)}.")
        if method_str not in _METHOD_MAP:
            raise ValueError(f"Invalid contour method '{method_str}'. Must be one of {list(_METHOD_MAP)}.")
        if thickness < 1 or thickness > 50:
            raise ValueError(f"thickness must be between 1 and 50, got {thickness}")

        mode = _MODE_MAP[mode_str]
        method = _METHOD_MAP[method_str]

        # Convert to single-channel for findContours
        if len(image.shape) == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif len(image.shape) == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        elif len(image.shape) == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
        elif len(image.shape) == 2:
            gray = image.copy()
        else:
            raise ValueError(f"Unsupported image shape {image.shape}.")

        # Normalize to uint8 — float images in [0,1] need scaling first
        if gray.dtype != np.uint8:
            if np.issubdtype(gray.dtype, np.floating):
                gray = (gray * 255.0 if gray.max() <= 1.0 else gray).clip(0, 255).astype(np.uint8)
            elif gray.dtype == np.uint16:
                gray = (gray >> 8).astype(np.uint8)
            else:
                gray = gray.astype(np.uint8)

        # Do not bake in opinionated thresholding/blur here.
        # findContours expects a binary mask or single-channel image directly.
        # Standard OpenCV behavior: non-zero pixels are treated as 1 (foreground).
        contours = cv2.findContours(gray, mode, method)[-2]

        # Build result canvas before checking contours so output shape is always consistent
        result = image.copy()
        if len(result.shape) == 2 or (len(result.shape) == 3 and result.shape[2] == 1):
            result = cv2.cvtColor(image if len(image.shape) == 2 else image[:, :, 0], cv2.COLOR_GRAY2BGR)
            draw_color = bgr_color
        elif len(result.shape) == 3 and result.shape[2] == 4:
            draw_color = (*bgr_color, 255)
        else:
            draw_color = bgr_color

        if not contours:
            return result

        cv2.drawContours(result, contours, -1, draw_color, thickness)
        return result
