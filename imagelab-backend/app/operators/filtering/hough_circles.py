import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


class HoughCircles(BaseOperator):
    """Detect circular objects in an image using the circular Hough transform.

    Converts the input to grayscale, runs cv2.HoughCircles using cv2.HOUGH_GRADIENT,
    and draws the detected circle outlines and optional center markers on a copy
    of the image. For grayscale input, returns a 3-channel BGR image so that colored
    annotations are visible. For 4-channel BGRA input, preserves the alpha channel.
    If no circles are detected, returns the image canvas unchanged.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("HoughCircles.compute: received an invalid or empty image")

        try:
            dp = float(self.params.get("dp", 1.2))
        except (TypeError, ValueError):
            dp = 1.2

        try:
            min_dist = float(self.params.get("minDist", 20.0))
        except (TypeError, ValueError):
            min_dist = 20.0

        try:
            param1 = float(self.params.get("param1", 100.0))
        except (TypeError, ValueError):
            param1 = 100.0

        try:
            param2 = float(self.params.get("param2", 30.0))
        except (TypeError, ValueError):
            param2 = 30.0

        try:
            min_radius = int(self.params.get("minRadius", 0))
        except (TypeError, ValueError):
            min_radius = 0

        try:
            max_radius = int(self.params.get("maxRadius", 0))
        except (TypeError, ValueError):
            max_radius = 0

        try:
            thickness = int(self.params.get("thickness", 2))
        except (TypeError, ValueError):
            thickness = 2

        try:
            center_radius = int(self.params.get("centerRadius", 3))
        except (TypeError, ValueError):
            center_radius = 3

        raw_draw_centers = self.params.get("drawCenters", True)
        draw_centers = (
            raw_draw_centers.lower() in ("true", "1", "yes")
            if isinstance(raw_draw_centers, str)
            else bool(raw_draw_centers)
        )

        # Validate parameter ranges
        if dp < 0.5 or dp > 10.0:
            raise ValueError(f"dp must be between 0.5 and 10.0, got {dp}")
        if min_dist < 1.0 or min_dist > 10000.0:
            raise ValueError(f"minDist must be between 1.0 and 10000.0, got {min_dist}")
        if param1 < 1.0 or param1 > 1000.0:
            raise ValueError(f"param1 must be between 1.0 and 1000.0, got {param1}")
        if param2 < 1.0 or param2 > 1000.0:
            raise ValueError(f"param2 must be between 1.0 and 1000.0, got {param2}")
        if min_radius < 0 or min_radius > 10000:
            raise ValueError(f"minRadius must be between 0 and 10000, got {min_radius}")
        if max_radius < 0 or max_radius > 10000:
            raise ValueError(f"maxRadius must be between 0 and 10000, got {max_radius}")
        if max_radius > 0 and min_radius > max_radius:
            raise ValueError(f"minRadius ({min_radius}) cannot be greater than maxRadius ({max_radius})")
        if thickness < 1 or thickness > 50:
            raise ValueError(f"thickness must be between 1 and 50, got {thickness}")
        if center_radius < 1 or center_radius > 50:
            raise ValueError(f"centerRadius must be between 1 and 50, got {center_radius}")

        raw_circle_color = self.params.get("circleColor") or self.params.get("color") or "#00ff00"
        circle_bgr = hex_to_bgr(raw_circle_color)

        raw_center_color = self.params.get("centerColor", "#ff0000")
        center_bgr = hex_to_bgr(raw_center_color)

        # Convert to single-channel 8-bit for Hough transform
        if image.ndim == 2:
            gray = image
        elif image.ndim == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
        elif image.ndim == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif image.ndim == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        else:
            raise ValueError(f"Unsupported image shape {image.shape}")

        if gray.dtype != np.uint8:
            if np.issubdtype(gray.dtype, np.floating):
                gray = (gray * 255.0 if gray.max() <= 1.0 else gray).clip(0, 255).astype(np.uint8)
            elif gray.dtype == np.uint16:
                gray = (gray >> 8).astype(np.uint8)
            else:
                gray = gray.astype(np.uint8)

        # Smooth image to reduce false circle detections
        blurred_gray = cv2.medianBlur(gray, 5)

        circles = cv2.HoughCircles(
            blurred_gray,
            cv2.HOUGH_GRADIENT,
            dp=dp,
            minDist=min_dist,
            param1=param1,
            param2=param2,
            minRadius=min_radius,
            maxRadius=max_radius,
        )

        # Prepare result canvas
        if image.ndim == 2 or (image.ndim == 3 and image.shape[2] == 1):
            base_gray = image if image.ndim == 2 else image[:, :, 0]
            result = cv2.cvtColor(base_gray, cv2.COLOR_GRAY2BGR)
            circle_color = circle_bgr
            center_color = center_bgr
        elif image.ndim == 3 and image.shape[2] == 4:
            result = image.copy()
            circle_color = (*circle_bgr, 255)
            center_color = (*center_bgr, 255)
        else:
            result = image.copy()
            circle_color = circle_bgr
            center_color = center_bgr

        if circles is None:
            return result

        circles = np.round(circles[0, :]).astype(int)
        for x, y, r in circles:
            cv2.circle(result, (int(x), int(y)), int(r), circle_color, thickness)
            if draw_centers:
                cv2.circle(result, (int(x), int(y)), center_radius, center_color, -1)

        return result
