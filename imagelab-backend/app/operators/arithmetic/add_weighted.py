import logging

import cv2
import numpy as np

from app.operators.base import BaseOperator

logger = logging.getLogger(__name__)


class ArithmeticAddWeighted(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        try:
            alpha = max(0.0, min(1.0, float(self.params.get("alpha", 0.5))))
            beta = float(self.params.get("beta", 1.0 - alpha))
            gamma = float(self.params.get("gamma", 0.0))

            src2 = self.params.get("image2")
            if src2 is None or not isinstance(src2, np.ndarray):
                src2 = image.copy()

            # 1. Match Spatial Dimensions
            if src2.shape[:2] != image.shape[:2]:
                src2 = cv2.resize(src2, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_AREA)

            # 2. Match Color Channels
            if src2.ndim != image.ndim:
                if image.ndim == 2 and src2.ndim == 3:
                    src2 = cv2.cvtColor(src2, cv2.COLOR_BGR2GRAY)
                elif image.ndim == 3 and src2.ndim == 2:
                    src2 = cv2.cvtColor(src2, cv2.COLOR_GRAY2BGR)

            # 3. Match Data Types & Ensure Memory Contiguity
            if src2.dtype != image.dtype:
                src2 = src2.astype(image.dtype)

            image_c = np.ascontiguousarray(image)
            src2_c = np.ascontiguousarray(src2)

            # 4. Explicit Output Depth
            return cv2.addWeighted(image_c, alpha, src2_c, beta, gamma, dtype=image_c.dtype)

        except Exception as err:
            # Log the exception and raise a clean, human-readable error
            logger.error(f"Failed to blend images in ArithmeticAddWeighted: {err}")
            raise ValueError(
                "Failed to blend branch outputs: mismatched image dimensions, channels, or data types."
            ) from err
