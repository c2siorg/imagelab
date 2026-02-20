import cv2
import numpy as np

from app.operators.base import BaseOperator

DISTANCE_TYPES = {
    "DIST_C": cv2.DIST_C,
    "DIST_L1": cv2.DIST_L1,
    "DIST_L2": cv2.DIST_L2,
    "DIST_LABEL_PIXEL": cv2.DIST_L2,
    "DIST_MASK_3": cv2.DIST_L2,
}


class DistanceTransform(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        dist_name = self.params.get("type", "DIST_L2")
        dist_type = DISTANCE_TYPES.get(dist_name, cv2.DIST_L2)

        # Convert to grayscale if needed
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        # Threshold to get binary image
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        dist = cv2.distanceTransform(binary, dist_type, maskSize=5)

        # Normalize to 0-255 uint8 for display
        cv2.normalize(dist, dist, 0, 255, cv2.NORM_MINMAX)
        return dist.astype(np.uint8)
