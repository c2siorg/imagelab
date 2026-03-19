import cv2
import numpy as np

from app.operators.base import BaseOperator


class KMeansSegmentation(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            gray = image if len(image.shape) == 2 else image[:, :, 0]
            image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        k = int(self.params.get("k", 3))
        k = max(2, min(10, k))

        max_iter = max(1, min(500, int(self.params.get("max_iter", 100))))
        epsilon = max(0.01, min(10.0, float(self.params.get("epsilon", 0.2))))
        attempts = max(1, min(10, int(self.params.get("attempts", 3))))

        pixel_values = image.reshape((-1, 3))
        pixel_values = np.float32(pixel_values)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, max_iter, epsilon)
        _, labels, centers = cv2.kmeans(pixel_values, k, None, criteria, attempts, cv2.KMEANS_RANDOM_CENTERS)

        centers = np.uint8(centers)
        segmented = centers[labels.flatten()]
        result = segmented.reshape(image.shape)

        return result
