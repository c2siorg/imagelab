import cv2
import numpy as np

from app.operators.base import BaseOperator


class AdaptiveThreshold(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        max_value = float(self.params.get("maxValue", 255))
        max_value = max(0, min(255, max_value))
        
        method_str = str(self.params.get("adaptiveMethod", "GAUSSIAN")).upper()
        adaptive_method = cv2.ADAPTIVE_THRESH_MEAN_C if method_str == "MEAN" else cv2.ADAPTIVE_THRESH_GAUSSIAN_C
            
        block_size = int(self.params.get("blockSize", 3))
        if block_size < 3:
            block_size = 3
        elif block_size % 2 == 0:
            block_size += 1
            
        c_value = float(self.params.get("cValue", 2))

        if len(image.shape) == 3:
            if image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            else:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                
        if image.dtype != np.uint8:
            image = image.astype(np.uint8)

        return cv2.adaptiveThreshold(
            image,
            max_value,
            adaptive_method,
            cv2.THRESH_BINARY,
            block_size,
            c_value,
        )
