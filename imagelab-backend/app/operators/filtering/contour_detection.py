import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr

MODE_MAP = {"EXTERNAL": cv2.RETR_EXTERNAL, "TREE": cv2.RETR_TREE}
METHOD_MAP = {"SIMPLE": cv2.CHAIN_APPROX_SIMPLE, "NONE": cv2.CHAIN_APPROX_NONE}


class ContourDetection(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        """
        Detect contours in a single-channel (binary/grayscale) image and draw
        them onto a copy of the input.

        Params:
            mode (str): "EXTERNAL" (outermost contours only) or "TREE" (full hierarchy).
            method (str): "SIMPLE" (compressed) or "NONE" (all contour points).
            rgbcolors_input (str): Hex color string for the drawn contours (e.g. "#00ff00").
            thickness (int): Stroke width in pixels (>= 1, <= 50).

        Note:
            Float images are scaled to [0, 255] before processing.
            Grayscale input is promoted to BGR in the returned image.
            Does not apply thresholding or blurring; the caller is responsible
            for ensuring the input is a suitable binary or edge mask.
        """
        mode_str = str(self.params.get("mode", "EXTERNAL")).upper()
        method_str = str(self.params.get("method", "SIMPLE")).upper()
        thickness = int(self.params.get("thickness", 2))
        hex_color = self.params.get("rgbcolors_input", "#00ff00")
        bgr_color = hex_to_bgr(hex_color)

        if mode_str not in MODE_MAP:
            raise ValueError(f"Invalid contour mode '{mode_str}'. Must be one of {list(MODE_MAP)}.")
        if method_str not in METHOD_MAP:
            raise ValueError(f"Invalid contour method '{method_str}'. Must be one of {list(METHOD_MAP)}.")
        mode = MODE_MAP[mode_str]
        method = METHOD_MAP[method_str]

        if thickness < 1:
            raise ValueError(f"thickness must be >= 1, got {thickness}")
        if thickness > 50:
            raise ValueError(f"thickness must be <= 50, got {thickness}")

        if image.ndim == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif image.ndim == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        elif image.ndim == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
        elif image.ndim == 2:
            gray = image.copy()
        else:
            raise ValueError(f"Unsupported image shape {image.shape}. Expected (H,W), (H,W,1), (H,W,3), or (H,W,4).")

        if gray.dtype != np.uint8:
            if np.issubdtype(gray.dtype, np.floating):
                if gray.max() <= 1.0:
                    gray = (gray * 255.0).clip(0, 255).astype(np.uint8)
                else:
                    gray = gray.clip(0, 255).astype(np.uint8)
            elif gray.dtype == np.uint16:
                gray = (gray >> 8).astype(np.uint8)
            else:
                gray = gray.astype(np.uint8)

        # Do not bake in opinionated thresholding/blur here.
        # findContours expects a binary mask or single-channel image directly.
        # Standard OpenCV behavior: non-zero pixels are treated as 1 (foreground).
        ret = cv2.findContours(gray, mode, method)
        contours = ret[-2]

        result = image.copy()
        if result.ndim == 2:
            result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
            draw_color = bgr_color
        elif result.ndim == 3 and result.shape[2] == 4:
            draw_color = (*bgr_color, 255)
        elif result.ndim == 3 and result.shape[2] == 1:
            result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
            draw_color = bgr_color
        else:
            draw_color = bgr_color

        if not contours:
            return result

        cv2.drawContours(result, contours, -1, draw_color, thickness)

        return result
