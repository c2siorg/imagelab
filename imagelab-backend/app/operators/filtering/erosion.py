import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.operators.filtering.validation import validate_anchor_point


class Erosion(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        iteration = max(1, int(self.params.get("iteration", 1)))
        point_x = int(self.params.get("point_x", -1))
        point_y = int(self.params.get("point_y", -1))
        kernel_size = max(1, int(self.params.get("kernelSize", 5)))
        if kernel_size % 2 == 0:
            kernel_size += 1
        validate_anchor_point(point_x, kernel_size, "point_x")
        validate_anchor_point(point_y, kernel_size, "point_y")
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        return cv2.erode(
            image,
            kernel,
            anchor=(point_x, point_y),
            iterations=iteration,
        )
