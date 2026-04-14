import cv2
import numpy as np

from app.operators.base import BaseOperator


class SaltPepperNoise(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        try:
            density = float(self.params.get("density", 0.05))
        except (TypeError, ValueError):
            density = 0.05
        density = max(0.0, min(1.0, density))

        seed = self.params.get("seed", None)
        rng = np.random.default_rng(int(seed) if seed is not None else None)

        alpha = None
        if len(image.shape) == 3 and image.shape[2] == 4:
            alpha = image[:, :, 3].copy()
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        result = image.copy()
        total_pixels = image.shape[0] * image.shape[1]
        num_affected = int(total_pixels * density)
        num_affected -= num_affected % 2  # ensure even split

        flat_indices = rng.choice(total_pixels, num_affected, replace=False)
        salt_flat = flat_indices[: num_affected // 2]
        pepper_flat = flat_indices[num_affected // 2 :]

        salt_rows, salt_cols = np.unravel_index(salt_flat, (image.shape[0], image.shape[1]))
        pepper_rows, pepper_cols = np.unravel_index(pepper_flat, (image.shape[0], image.shape[1]))

        result[salt_rows, salt_cols] = 255
        result[pepper_rows, pepper_cols] = 0

        if alpha is not None:
            result = np.dstack([result, alpha])

        return result
