import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.operators.filtering.validation import validate_anchor_point, validate_positive_kernel_dim


class BoxFilter(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        width = int(self.params.get("width", 3))
        height = int(self.params.get("height", 3))
        depth = int(self.params.get("depth", -1))  # -1 = preserve source image depth (OpenCV convention)
        point_x = int(self.params.get("point_x", -1))
        point_y = int(self.params.get("point_y", -1))

        validate_positive_kernel_dim(width, "width")
        validate_positive_kernel_dim(height, "height")
        validate_anchor_point(point_x, width, "point_x")
        validate_anchor_point(point_y, height, "point_y")

        return cv2.boxFilter(
            image,
            depth,
            (width, height),  # OpenCV ksize convention: (width, height)
            anchor=(point_x, point_y),
            normalize=True,
            borderType=cv2.BORDER_DEFAULT,
        )
