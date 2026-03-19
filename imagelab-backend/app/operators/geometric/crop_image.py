import numpy as np

from app.operators.base import BaseOperator


class CropImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        height, width = image.shape[:2]

        # Get cropping coordinates from parameters with defaults
        x1 = int(self.params.get("x1", 0))
        y1 = int(self.params.get("y1", 0))
        x2 = int(self.params.get("x2", image.shape[1]))
        y2 = int(self.params.get("y2", image.shape[0]))

        # Clamp to boundaries (Requirement: No out-of-bounds)
        x1 = max(0, min(x1, width))
        y1 = max(0, min(y1, height))
        x2 = max(0, min(x2, width))
        y2 = max(0, min(y2, height))

        # If the coordinates are invalid return the original image
        if x1 >= x2 or y1 >= y2:
            return image

        # Image slicing in OpenCV is image[y1:y2, x1:x2]
        cropped_image = image[y1:y2, x1:x2]
        return cropped_image
