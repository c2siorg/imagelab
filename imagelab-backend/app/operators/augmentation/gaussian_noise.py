import cv2
import numpy as np

from app.operators.base import BaseOperator


class GaussianNoise(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        try:
            mean = float(self.params.get("mean", 0))
        except (TypeError, ValueError):
            mean = 0.0

        try:
            sigma = float(self.params.get("sigma", 25))
        except (TypeError, ValueError):
            sigma = 25.0
        sigma = max(1.0, sigma)

        seed = self.params.get("seed", None)
        rng = np.random.default_rng(int(seed) if seed is not None else None)

        alpha = None
        if len(image.shape) == 3 and image.shape[2] == 4:
            alpha = image[:, :, 3].copy()
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        noise = rng.normal(mean, sigma, image.shape).astype(np.float32)
        noisy = np.clip(image.astype(np.float32) + noise, 0, 255).astype(np.uint8)

        if alpha is not None:
            noisy = np.dstack([noisy, alpha])

        return noisy
