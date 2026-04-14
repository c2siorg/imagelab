import cv2
import numpy as np

from app.operators.base import BaseOperator


class Watershed(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            gray = image if len(image.shape) == 2 else image[:, :, 0]
            image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)

        sure_bg = cv2.dilate(opening, kernel, iterations=3)

        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)

        dist_max = dist_transform.max()
        if dist_max == 0:
            return image.copy()

        foreground_threshold = float(self.params.get("foreground_threshold", 0.5))
        foreground_threshold = max(0.1, min(0.9, foreground_threshold))
        _, sure_fg = cv2.threshold(dist_transform, foreground_threshold * dist_max, 255, 0)
        sure_fg = np.uint8(sure_fg)

        unknown = cv2.subtract(sure_bg, sure_fg)

        _, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0

        markers = cv2.watershed(image, markers)

        result = image.copy()
        boundary_mask = markers == -1

        thick_kernel = np.ones((5, 5), np.uint8)
        thick_boundary = cv2.dilate(boundary_mask.astype(np.uint8), thick_kernel, iterations=1)

        result[thick_boundary == 1] = [0, 0, 255]

        return result
