from typing import Any

import cv2
import numpy as np

from app.operators.base import BaseOperator

MORPH_TYPES = {
    "OPEN": cv2.MORPH_OPEN,
    "CLOSE": cv2.MORPH_CLOSE,
    "GRADIENT": cv2.MORPH_GRADIENT,
    "TOPHAT": cv2.MORPH_TOPHAT,
    "BLACKHAT": cv2.MORPH_BLACKHAT,
}

NEEDS_RGB_CONVERSION = {"GRADIENT", "TOPHAT", "BLACKHAT"}


def _validate_kernel_size(value: Any) -> int:
    # bool is a subclass of int in Python; True/False must be rejected explicitly
    if isinstance(value, bool):
        raise ValueError(f"kernelSize must be a positive odd integer, got bool ({value!r})")

    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError(f"kernelSize must be a positive odd integer, got non-integer float ({value!r})")
        parsed = int(value)
    else:
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"kernelSize must be a positive odd integer, got {type(value).__name__} ({value!r})"
            ) from exc

    if parsed <= 0:
        raise ValueError(f"kernelSize must be positive, got {parsed}")
    if parsed % 2 == 0:
        raise ValueError(f"kernelSize must be odd, got {parsed}")

    return parsed


class Morphological(BaseOperator):
    def __init__(self, params: dict) -> None:
        super().__init__(params)
        # Validate eagerly at construction time so misconfigured params fail fast
        self._kernel_size = _validate_kernel_size(params.get("kernelSize", 5))

    def compute(self, image: np.ndarray) -> np.ndarray:
        morph_name = self.params.get("type", "TOPHAT")
        morph_type = MORPH_TYPES.get(morph_name, cv2.MORPH_TOPHAT)
        # Convert RGBA to RGB for certain morph types
        if morph_name in NEEDS_RGB_CONVERSION and len(image.shape) == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        kernel = np.ones((self._kernel_size, self._kernel_size), np.uint8)
        return cv2.morphologyEx(image, morph_type, kernel)
