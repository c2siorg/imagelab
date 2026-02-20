import cv2
import numpy as np

from app.operators.base import BaseOperator

FLIP_CODES = {
    "X": 0,
    "Y": 1,
    "Both": -1,
}


class ReflectImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        flip_type = self.params.get("type", "X")
        flip_code = FLIP_CODES.get(flip_type, 0)
        return cv2.flip(image, flip_code)
