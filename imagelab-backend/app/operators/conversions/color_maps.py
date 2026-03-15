import cv2
import numpy as np

from app.operators.base import BaseOperator

COLORMAP_TYPES = {
    "HOT": cv2.COLORMAP_HOT,
    "AUTUMN": cv2.COLORMAP_AUTUMN,
    "BONE": cv2.COLORMAP_BONE,
    "COOL": cv2.COLORMAP_COOL,
    "HSV": cv2.COLORMAP_HSV,
    "JET": cv2.COLORMAP_JET,
    "OCEAN": cv2.COLORMAP_OCEAN,
    "PARULA": cv2.COLORMAP_PARULA,
    "PINK": cv2.COLORMAP_PINK,
    "RAINBOW": cv2.COLORMAP_RAINBOW,
}


class ColorMaps(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        colormap_name = self.params.get("type", "HOT")
        colormap = COLORMAP_TYPES.get(colormap_name, cv2.COLORMAP_HOT)

        # cv2.applyColorMap requires a single-channel grayscale image
        if len(image.shape) == 3:
            if image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            else:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        return cv2.applyColorMap(image, colormap)
