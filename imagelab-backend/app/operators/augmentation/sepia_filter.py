import cv2
import numpy as np

from app.operators.base import BaseOperator


class SepiaFilter(BaseOperator):
    _SEPIA_MATRIX = np.array(
        [
            [0.131, 0.534, 0.272],
            [0.168, 0.686, 0.349],
            [0.189, 0.769, 0.393],
        ],
        dtype=np.float32,
    )

    def compute(self, image: np.ndarray) -> np.ndarray:
        try:
            intensity = float(self.params.get("intensity", 1.0))
        except (TypeError, ValueError):
            intensity = 1.0
        intensity = max(0.0, min(1.0, intensity))

        if intensity == 0.0:
            return image.copy()

        alpha = None
        if len(image.shape) == 3 and image.shape[2] == 4:
            alpha = image[:, :, 3].copy()
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        elif len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        img_f = image.astype(np.float32)
        sepia_f = cv2.transform(img_f, self._SEPIA_MATRIX)
        sepia_f = np.clip(sepia_f, 0, 255)

        result = ((1.0 - intensity) * img_f + intensity * sepia_f).astype(np.uint8)

        if alpha is not None:
            result = cv2.merge([result[:, :, 0], result[:, :, 1], result[:, :, 2], alpha])

        return result
