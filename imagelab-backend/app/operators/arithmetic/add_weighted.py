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
            ch_img = 1 if image.ndim == 2 else image.shape[2]
            ch_src2 = 1 if src2.ndim == 2 else src2.shape[2]
            if ch_src2 != ch_img:
                from app.services.pipeline_executor import harmonize_image_channels

                src2 = harmonize_image_channels(src2, ch_img)

            # 3. Match Data Types & Ensure Memory Contiguity
            if src2.dtype != image.dtype:
                src2 = src2.astype(image.dtype)

            image_c = np.ascontiguousarray(image)
            src2_c = np.ascontiguousarray(src2)

            # 4. Explicit Output Depth (-1 preserves destination depth in OpenCV)
            return cv2.addWeighted(image_c, alpha, src2_c, beta, gamma, dtype=-1)

        except Exception as err:
            # Log the exception and raise a clean, human-readable error
            logger.error(f"Failed to blend images in ArithmeticAddWeighted: {err}")
            raise ValueError(
                "Failed to blend branch outputs: mismatched image dimensions, channels, or data types."
            ) from err
