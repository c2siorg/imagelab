import cv2
import numpy as np

from app.operators.base import BaseOperator


class BgrToYcrcb(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif len(image.shape) == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            
        return cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
