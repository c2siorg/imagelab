import cv2
import numpy as np

from app.operators.base import BaseOperator

THRESHOLD_TYPES = {
    "threshold_binary": cv2.THRESH_BINARY,
    "threshold_binary_inv": cv2.THRESH_BINARY_INV,
}


class ColorToBinary(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        threshold_type_name = self.params.get("thresholdType", "threshold_binary")
        threshold_type = THRESHOLD_TYPES.get(threshold_type_name, cv2.THRESH_BINARY)
        threshold_value = float(self.params.get("thresholdValue", 0))
        max_value = float(self.params.get("maxValue", 255))

        if image.ndim == 2:
            gray = image
        elif image.ndim == 3:
            channels = image.shape[2]
            if channels == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            elif channels == 4:
                gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            elif channels == 1:
                gray = image[:, :, 0]
            else:
                raise ValueError(
                    f"ColorToBinary expects 1, 3, or 4 channels, got shape={image.shape}."
                )
        else:
            raise ValueError(
                f"ColorToBinary expects a 2-D or 3-D array, got ndim={image.ndim}."
            )

        _, dst = cv2.threshold(gray, threshold_value, max_value, threshold_type)
        return dst
