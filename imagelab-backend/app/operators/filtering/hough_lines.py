import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr

# Canny preprocessing is fixed; the block only exposes the Hough parameters.
_CANNY_THRESHOLD1 = 50
_CANNY_THRESHOLD2 = 150
_CANNY_APERTURE_SIZE = 3


class HoughLines(BaseOperator):
    """Detect straight line segments with the probabilistic Hough transform.

    Runs Canny on a grayscale copy of the input, feeds the edge map to
    cv2.HoughLinesP and draws the detected segments onto a copy of the
    original image. If no segments are found, the image comes back unchanged.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        rho = float(self.params.get("rho", 1.0))
        theta_degrees = float(self.params.get("thetaDegrees", 1.0))
        threshold = int(self.params.get("threshold", 50))
        min_line_length = int(self.params.get("minLineLength", 50))
        max_line_gap = int(self.params.get("maxLineGap", 10))
        bgr_color = hex_to_bgr(self.params.get("color", "#00ff00"))
        thickness = int(self.params.get("thickness", 2))

        # Ranges mirror the block's field limits. rho and thetaDegrees also size the
        # Hough accumulator, so the lower bounds keep memory use bounded.
        if rho < 0.1 or rho > 10:
            raise ValueError(f"rho must be between 0.1 and 10, got {rho}")
        if theta_degrees < 0.1 or theta_degrees > 180:
            raise ValueError(f"thetaDegrees must be between 0.1 and 180, got {theta_degrees}")
        if threshold < 1 or threshold > 1000:
            raise ValueError(f"threshold must be between 1 and 1000, got {threshold}")
        if min_line_length < 0 or min_line_length > 10000:
            raise ValueError(f"minLineLength must be between 0 and 10000, got {min_line_length}")
        if max_line_gap < 0 or max_line_gap > 10000:
            raise ValueError(f"maxLineGap must be between 0 and 10000, got {max_line_gap}")
        if thickness < 1 or thickness > 50:
            raise ValueError(f"thickness must be between 1 and 50, got {thickness}")

        theta = np.deg2rad(theta_degrees)

        # Convert to single-channel for Canny
        if len(image.shape) == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif len(image.shape) == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        elif len(image.shape) == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
        elif len(image.shape) == 2:
            gray = image
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

        edges = cv2.Canny(gray, _CANNY_THRESHOLD1, _CANNY_THRESHOLD2, apertureSize=_CANNY_APERTURE_SIZE)
        lines = cv2.HoughLinesP(
            edges,
            rho,
            theta,
            threshold,
            minLineLength=min_line_length,
            maxLineGap=max_line_gap,
        )

        # Build result canvas before checking lines so output shape is always consistent
        result = image.copy()
        if len(result.shape) == 2 or (len(result.shape) == 3 and result.shape[2] == 1):
            result = cv2.cvtColor(image if len(image.shape) == 2 else image[:, :, 0], cv2.COLOR_GRAY2BGR)
            draw_color = bgr_color
        elif len(result.shape) == 3 and result.shape[2] == 4:
            draw_color = (*bgr_color, 255)
        else:
            draw_color = bgr_color

        if lines is None:
            return result

        for x1, y1, x2, y2 in lines[:, 0]:
            cv2.line(result, (int(x1), int(y1)), (int(x2), int(y2)), draw_color, thickness)
        return result
