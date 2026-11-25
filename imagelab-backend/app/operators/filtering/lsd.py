import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr

_REFINE_MAP: dict[str, int] = {
    "NONE": cv2.LSD_REFINE_NONE,
    "STD": cv2.LSD_REFINE_STD,
    "ADV": cv2.LSD_REFINE_ADV,
}


class LineSegmentDetector(BaseOperator):
    """Detect straight line segments with sub-pixel accuracy using LSD.

    Runs cv2.createLineSegmentDetector on a grayscale version of the image and
    renders the detected line segments onto the output canvas.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("LineSegmentDetector.compute: received an invalid or empty image")

        if not (image.ndim == 2 or (image.ndim == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(
                f"LineSegmentDetector expects a 2-D or 3-D image with 1, 3, or 4 channels, got shape {image.shape}."
            )

        if image.dtype != np.uint8:
            raise ValueError(f"LineSegmentDetector expects a uint8 image, got dtype={image.dtype}.")

        refine_str = str(self.params.get("refine", "STD")).upper()
        refine = _REFINE_MAP.get(refine_str, cv2.LSD_REFINE_STD)

        try:
            scale = float(self.params.get("scale", 0.8))
        except (TypeError, ValueError):
            scale = 0.8
        scale = max(0.1, min(2.0, scale))

        try:
            thickness = int(self.params.get("thickness", 2))
        except (TypeError, ValueError):
            thickness = 2
        thickness = max(1, min(20, thickness))

        color_hex = str(self.params.get("lineColor", "#00FF00"))
        bgr_color = hex_to_bgr(color_hex)

        # Convert to grayscale for LSD detection
        if image.ndim == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            draw_canvas = image[:, :, :3].copy()
            draw_color = bgr_color
            has_alpha = True
        elif image.ndim == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            draw_canvas = image.copy()
            draw_color = bgr_color
            has_alpha = False
        elif image.ndim == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
            draw_canvas = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            draw_color = bgr_color
            has_alpha = False
        else:
            gray = image
            draw_canvas = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            draw_color = bgr_color
            has_alpha = False

        detector = cv2.createLineSegmentDetector(refine=refine, scale=scale)
        lines, _, _, _ = detector.detect(gray)

        if lines is not None:
            for x1, y1, x2, y2 in lines[:, 0]:
                pt1 = (int(round(float(x1))), int(round(float(y1))))
                pt2 = (int(round(float(x2))), int(round(float(y2))))
                cv2.line(draw_canvas, pt1, pt2, draw_color, thickness)

        if has_alpha:
            return np.dstack([draw_canvas, image[:, :, 3]])

        return draw_canvas
