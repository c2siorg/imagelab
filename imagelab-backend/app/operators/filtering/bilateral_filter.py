import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.operators.filtering.validation import (
    validate_positive_kernel_dim,
    validate_positive_number,
)


class BilateralFilter(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        filter_size = int(self.params.get("filterSize", 5))
        sigma_color = float(self.params.get("sigmaColor", 75))
        sigma_space = float(self.params.get("sigmaSpace", 75))

        # Validate parameters before passing to OpenCV
        validate_positive_kernel_dim(filter_size, "filterSize")
        validate_positive_number(sigma_color, "sigmaColor")
        validate_positive_number(sigma_space, "sigmaSpace")

        if image.ndim == 3 and image.shape[2] == 4:
            bgr = image[:, :, :3]
            res_bgr = cv2.bilateralFilter(bgr, filter_size, sigma_color, sigma_space)
            return np.dstack([res_bgr, image[:, :, 3]])

        if image.ndim == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
            res_gray = cv2.bilateralFilter(gray, filter_size, sigma_color, sigma_space)
            return res_gray[:, :, np.newaxis]

        return cv2.bilateralFilter(image, filter_size, sigma_color, sigma_space)
