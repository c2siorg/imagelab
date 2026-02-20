import cv2
import numpy as np

from app.operators.base import BaseOperator


class Blur(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        width_size = int(self.params.get("widthSize", 3))
        height_size = int(self.params.get("heightSize", 3))
        point_x = int(self.params.get("pointX", -1))
        point_y = int(self.params.get("pointY", -1))
        return cv2.blur(
            image,
            (height_size, width_size),
            anchor=(point_x, point_y),
            borderType=cv2.BORDER_DEFAULT,
        )
