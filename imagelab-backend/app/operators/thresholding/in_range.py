from typing import Any

import cv2
import numpy as np

from app.operators.base import BaseOperator

VALID_OUTPUT_MODES = {"mask", "masked_image"}


def _validate_channel_bound(value: Any, name: str) -> int:
    """Validate and clamp channel threshold bounds to integer [0, 255]."""
    if isinstance(value, bool):
        raise ValueError(f"'{name}' must be an integer in range [0, 255], got boolean {value!r}")

    try:
        num = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"'{name}' must be numeric, got {type(value).__name__} ({value!r})") from exc

    clamped = max(0, min(255, int(round(num))))
    return clamped


class InRangeThreshold(BaseOperator):
    """Multi-channel range thresholding and color masking operator using cv2.inRange."""

    def __init__(self, params: dict) -> None:
        super().__init__(params)
        self.output_mode = str(self.params.get("outputMode", "mask")).strip().lower()
        if self.output_mode not in VALID_OUTPUT_MODES:
            raise ValueError(f"Invalid outputMode '{self.output_mode}'. Expected one of {sorted(VALID_OUTPUT_MODES)}")

        self.lower1 = _validate_channel_bound(self.params.get("lower1", 0), "lower1")
        self.upper1 = _validate_channel_bound(self.params.get("upper1", 255), "upper1")
        self.lower2 = _validate_channel_bound(self.params.get("lower2", 0), "lower2")
        self.upper2 = _validate_channel_bound(self.params.get("upper2", 255), "upper2")
        self.lower3 = _validate_channel_bound(self.params.get("lower3", 0), "lower3")
        self.upper3 = _validate_channel_bound(self.params.get("upper3", 255), "upper3")

        if self.lower1 > self.upper1:
            raise ValueError(f"lower1 ({self.lower1}) cannot exceed upper1 ({self.upper1})")
        if self.lower2 > self.upper2:
            raise ValueError(f"lower2 ({self.lower2}) cannot exceed upper2 ({self.upper2})")
        if self.lower3 > self.upper3:
            raise ValueError(f"lower3 ({self.lower3}) cannot exceed upper3 ({self.upper3})")

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or image.size == 0:
            raise ValueError("Input image cannot be empty or None")

        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8)

        is_grayscale = image.ndim == 2 or (image.ndim == 3 and image.shape[2] == 1)

        if is_grayscale:
            gray = image if image.ndim == 2 else image[:, :, 0]
            lower = np.array([self.lower1], dtype=np.uint8)
            upper = np.array([self.upper1], dtype=np.uint8)
            mask = cv2.inRange(gray, lower, upper)

            if self.output_mode == "mask":
                return mask

            masked = cv2.bitwise_and(gray, gray, mask=mask)
            if image.ndim == 3:
                return masked[:, :, np.newaxis]
            return masked

        num_channels = image.shape[2]
        if num_channels == 4:
            bgr = image[:, :, :3]
            alpha = image[:, :, 3]
            lower = np.array([self.lower1, self.lower2, self.lower3], dtype=np.uint8)
            upper = np.array([self.upper1, self.upper2, self.upper3], dtype=np.uint8)
            mask = cv2.inRange(bgr, lower, upper)

            if self.output_mode == "mask":
                return mask

            masked_bgr = cv2.bitwise_and(bgr, bgr, mask=mask)
            masked_alpha = cv2.bitwise_and(alpha, alpha, mask=mask)
            return np.dstack([masked_bgr, masked_alpha])

        if num_channels == 3:
            lower = np.array([self.lower1, self.lower2, self.lower3], dtype=np.uint8)
            upper = np.array([self.upper1, self.upper2, self.upper3], dtype=np.uint8)
            mask = cv2.inRange(image, lower, upper)

            if self.output_mode == "mask":
                return mask

            return cv2.bitwise_and(image, image, mask=mask)

        raise ValueError(f"Unsupported channel count: {num_channels}")
