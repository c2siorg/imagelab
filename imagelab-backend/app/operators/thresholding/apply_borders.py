import cv2
import numpy as np

from app.operators.base import BaseOperator


class ApplyBorders(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        border_all = self.params.get("border_all_sides")
        if border_all is not None:
            top = bottom = left = right = int(border_all)
        else:
            top = int(self.params.get("borderTop", 0))
            bottom = int(self.params.get("borderBottom", 0))
            left = int(self.params.get("borderLeft", 0))
            right = int(self.params.get("borderRight", 0))
        return cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0])
