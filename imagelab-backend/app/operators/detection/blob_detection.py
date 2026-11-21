import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


def _safe_float(val: object, default: float) -> float:
    try:
        return float(str(val).strip())
    except (TypeError, ValueError):
        return default


def _safe_bool(val: object, default: bool = False) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().upper() == "TRUE"
    return default


class BlobDetection(BaseOperator):
    """Detects blobs (regions differing in brightness or shape) using cv2.SimpleBlobDetector.

    Configures OpenCV's SimpleBlobDetector with filters for area, circularity,
    convexity, and inertia ratio, then renders rich keypoint markers indicating
    blob location, size, and orientation.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("BlobDetection received an invalid or empty image.")

        if not (image.ndim == 2 or (image.ndim == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(
                f"BlobDetection expects a 2-D or 3-D image with 1, 3, or 4 channels, got shape {image.shape}."
            )

        if image.dtype != np.uint8:
            raise ValueError(f"BlobDetection expects a uint8 image, got dtype={image.dtype}.")

        min_threshold = max(0.0, min(254.0, _safe_float(self.params.get("min_threshold", 10.0), 10.0)))
        max_threshold = max(1.0, min(255.0, _safe_float(self.params.get("max_threshold", 200.0), 200.0)))
        if min_threshold >= max_threshold:
            min_threshold, max_threshold = min(min_threshold, max_threshold), max(min_threshold, max_threshold)
            if min_threshold >= max_threshold:
                min_threshold = max(0.0, max_threshold - 1.0)
                if min_threshold == max_threshold:
                    max_threshold = min_threshold + 1.0

        filter_by_area = _safe_bool(self.params.get("filter_by_area", True), True)
        min_area = max(1.0, min(100000.0, _safe_float(self.params.get("min_area", 20.0), 20.0)))
        max_area = max(1.0, min(100000.0, _safe_float(self.params.get("max_area", 50000.0), 50000.0)))
        if min_area > max_area:
            min_area, max_area = max_area, min_area

        filter_by_circularity = _safe_bool(self.params.get("filter_by_circularity", False), False)
        min_circularity = max(0.01, min(1.0, _safe_float(self.params.get("min_circularity", 0.7), 0.7)))

        filter_by_convexity = _safe_bool(self.params.get("filter_by_convexity", False), False)
        min_convexity = max(0.01, min(1.0, _safe_float(self.params.get("min_convexity", 0.8), 0.8)))

        filter_by_inertia = _safe_bool(self.params.get("filter_by_inertia", False), False)
        min_inertia = max(0.01, min(1.0, _safe_float(self.params.get("min_inertia_ratio", 0.1), 0.1)))

        bgr_color = hex_to_bgr(str(self.params.get("rgbcolors_input", "#00ffff")))

        # Configure SimpleBlobDetector parameters
        detector_params = cv2.SimpleBlobDetector_Params()
        detector_params.minThreshold = float(min_threshold)
        detector_params.maxThreshold = float(max_threshold)
        detector_params.thresholdStep = 10.0

        detector_params.filterByColor = False

        detector_params.filterByArea = bool(filter_by_area)
        detector_params.minArea = float(min_area)
        detector_params.maxArea = float(max_area)

        detector_params.filterByCircularity = bool(filter_by_circularity)
        detector_params.minCircularity = float(min_circularity)
        detector_params.maxCircularity = 1.0

        detector_params.filterByConvexity = bool(filter_by_convexity)
        detector_params.minConvexity = float(min_convexity)
        detector_params.maxConvexity = 1.0

        detector_params.filterByInertia = bool(filter_by_inertia)
        detector_params.minInertiaRatio = float(min_inertia)
        detector_params.maxInertiaRatio = 1.0

        detector = cv2.SimpleBlobDetector_create(detector_params)

        # Prepare grayscale image for detection and base BGR image for rendering
        if image.ndim == 2:
            gray = image
            base_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            alpha = None
        elif image.ndim == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
            base_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            alpha = None
        elif image.ndim == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            base_bgr = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            alpha = image[:, :, 3]
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            base_bgr = image.copy()
            alpha = None

        keypoints = detector.detect(gray)

        drawn = cv2.drawKeypoints(
            base_bgr,
            keypoints,
            None,
            color=bgr_color,
            flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS,
        )

        if alpha is not None:
            return np.dstack((drawn, alpha))
        return drawn
