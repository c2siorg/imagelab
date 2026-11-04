import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


def _safe_int(val: object, default: int, min_val: int | None = None, max_val: int | None = None) -> int:
    try:
        res = int(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        res = default
    if min_val is not None:
        res = max(min_val, res)
    if max_val is not None:
        res = min(max_val, res)
    return res


def _safe_float(val: object, default: float, min_val: float | None = None, max_val: float | None = None) -> float:
    try:
        res = float(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        res = default
    if min_val is not None:
        res = max(min_val, res)
    if max_val is not None:
        res = min(max_val, res)
    return res


class OrbDetection(BaseOperator):
    """Detect and visualize local invariant features using ORB.

    Oriented FAST and Rotated BRIEF (ORB) detects keypoints across scale-space
    pyramids, computes directional orientation angles, and renders feature markers
    with optional scale circles and orientation vectors.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("OrbDetection received an invalid or empty image.")

        if not (image.ndim == 2 or (image.ndim == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(
                f"OrbDetection expects a 2-D or 3-D image with 1, 3, or 4 channels, got shape {image.shape}."
            )

        if image.dtype != np.uint8:
            raise ValueError(f"OrbDetection expects a uint8 image, got dtype={image.dtype}.")

        nfeatures = _safe_int(self.params.get("nfeatures", 500), default=500, min_val=1, max_val=2000)
        scale_factor = _safe_float(self.params.get("scaleFactor", 1.2), default=1.2, min_val=1.05, max_val=2.0)
        nlevels = _safe_int(self.params.get("nlevels", 8), default=8, min_val=1, max_val=16)

        min_dim = min(image.shape[:2])
        max_edge = max(2, min(min_dim // 2, 64))
        edge_threshold = _safe_int(self.params.get("edgeThreshold", 31), default=31, min_val=2, max_val=max_edge)
        fast_threshold = _safe_int(self.params.get("fastThreshold", 20), default=20, min_val=1, max_val=100)

        patch_size = edge_threshold
        max_levels = 1
        cur_dim = min_dim / patch_size
        while cur_dim >= scale_factor and max_levels < 16:
            cur_dim /= scale_factor
            max_levels += 1
        nlevels = max(1, min(nlevels, max_levels))

        raw_score = str(self.params.get("scoreType", "HARRIS_SCORE")).upper()
        score_type = cv2.ORB_FAST_SCORE if raw_score == "FAST_SCORE" else cv2.ORB_HARRIS_SCORE

        raw_rich = self.params.get("drawRichKeypoints", True)
        draw_rich = raw_rich.lower() in ("true", "1", "yes") if isinstance(raw_rich, str) else bool(raw_rich)

        raw_color = self.params.get("color") or self.params.get("rgbcolors_input") or "#00ff00"
        bgr_color = hex_to_bgr(raw_color)

        # Standardize grayscale representation for feature detection
        if image.ndim == 2:
            gray = image
            canvas = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            draw_color = bgr_color
        elif image.ndim == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
            canvas = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            draw_color = bgr_color
        elif image.ndim == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            canvas = image.copy()
            draw_color = (*bgr_color, 255)
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            canvas = image.copy()
            draw_color = bgr_color

        orb = cv2.ORB_create(
            nfeatures=nfeatures,
            scaleFactor=scale_factor,
            nlevels=nlevels,
            edgeThreshold=edge_threshold,
            firstLevel=0,
            WTA_K=2,
            scoreType=score_type,
            patchSize=patch_size,
            fastThreshold=fast_threshold,
        )

        keypoints = orb.detect(gray, None)

        if not keypoints:
            return canvas

        flags = cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS if draw_rich else cv2.DRAW_MATCHES_FLAGS_DEFAULT

        result = cv2.drawKeypoints(canvas, keypoints, None, color=draw_color, flags=flags)
        return result
