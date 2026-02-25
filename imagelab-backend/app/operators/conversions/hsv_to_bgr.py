import cv2
import numpy as np

from app.operators.base import BaseOperator


class HsvToBgr(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            
        if len(image.shape) == 3 and image.shape[2] >= 3:
            if image.shape[2] == 4:
                image = image[:, :, :3]
            return cv2.cvtColor(image, cv2.COLOR_HSV2BGR)
            
        return image
