import cv2
import numpy as np

from app.operators.base import BaseOperator

DISTANCE_TYPES = {
    "DIST_C": cv2.DIST_C,
    "DIST_L1": cv2.DIST_L1,
    "DIST_L2": cv2.DIST_L2,
}

MASK_SIZES = {3: 3, 5: 5}


class DistanceTransform(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        dist_name = self.params.get("type", "DIST_L2")
        dist_type = DISTANCE_TYPES.get(dist_name, cv2.DIST_L2)

        mask_size_param = int(self.params.get("maskSize", 5))
        mask_size = MASK_SIZES.get(mask_size_param, 5)

        # Convert to grayscale based on number of channels
        if len(image.shape) == 3:
            if image.shape[2] == 4:
                gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            else:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Threshold to get binary image
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        dist = cv2.distanceTransform(binary, dist_type, maskSize=mask_size)

        # Normalize to 0-255 uint8 for display
        cv2.normalize(dist, dist, 0, 255, cv2.NORM_MINMAX)
        return dist.astype(np.uint8)
