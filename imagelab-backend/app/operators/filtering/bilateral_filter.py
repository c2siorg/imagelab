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

        # Convert RGBA to BGR if needed
        if len(image.shape) == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        return cv2.bilateralFilter(image, filter_size, sigma_color, sigma_space)
