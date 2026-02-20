import cv2
import numpy as np

from app.operators.base import BaseOperator


class Dilation(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        iteration = int(self.params.get("iteration", 1))
        point_x = int(self.params.get("point_x", -1))
        point_y = int(self.params.get("point_y", -1))
        kernel = np.ones((5, 5), np.uint8)
        return cv2.dilate(
            image,
            kernel,
            anchor=(point_x, point_y),
            iterations=iteration,
        )
