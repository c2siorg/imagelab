import cv2
import numpy as np

from app.operators.base import BaseOperator

MAX_KERNEL_SIZE = 31
MAX_PROCESSING_DIM = 800


class GaborFilter(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        kernel_size = int(self.params.get("kernelSize", 21))
        sigma = max(0.1, float(self.params.get("sigma", 5.0)))
        theta = float(self.params.get("theta", 0.0))
        lambda_ = max(1.0, float(self.params.get("lambda", 10.0)))
        gamma = max(0.01, float(self.params.get("gamma", 0.5)))

        kernel_size = max(1, min(kernel_size, MAX_KERNEL_SIZE))
        if kernel_size % 2 == 0:
            kernel_size = max(1, kernel_size - 1)

        if len(image.shape) == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        original_h, original_w = image.shape[:2]

        if original_w == 0 or original_h == 0:
            raise ValueError(f"GaborFilter received an image with invalid dimensions: {original_w}x{original_h}")

        scale = min(MAX_PROCESSING_DIM / original_w, MAX_PROCESSING_DIM / original_h, 1.0)
        if scale < 1.0:
            small_w = max(1, int(original_w * scale))
            small_h = max(1, int(original_h * scale))
            working = cv2.resize(image, (small_w, small_h), interpolation=cv2.INTER_AREA)
        else:
            working = image

        kernel = cv2.getGaborKernel(
            (kernel_size, kernel_size),
            sigma,
            np.deg2rad(theta),
            lambda_,
            gamma,
            psi=0,
            ktype=cv2.CV_32F,
        )

        gray = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY) if len(working.shape) == 3 else working
        filtered = cv2.filter2D(gray.astype(np.float32), cv2.CV_32F, kernel)
        result_gray = cv2.normalize(np.abs(filtered), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        result_small = cv2.cvtColor(result_gray, cv2.COLOR_GRAY2BGR)

        if scale < 1.0:
            return cv2.resize(result_small, (original_w, original_h), interpolation=cv2.INTER_LINEAR)
        return result_small
