import cv2
import numpy as np

from app.operators.base import BaseOperator


class ContourDetection(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        color = self.params.get("color", "#00FF00")
        thickness = int(self.params.get("thickness", 1))
        mode = self.params.get("mode", "EXTERNAL")
        method = self.params.get("method", "SIMPLE")

        # Convert hex color to BGR
        hex_color = color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        color = (b, g, r)
        
        # Convert RGBA to BGR if needed
        if len(image.shape) == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        #Convert to grayscale if the image is not already
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        _,thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        if mode == "TREE":
            mode = cv2.RETR_TREE
        elif mode == "LIST":
            mode = cv2.RETR_LIST
        else:
            mode = cv2.RETR_EXTERNAL

        if method == "NONE":
            method = cv2.CHAIN_APPROX_NONE
        else:
            method = cv2.CHAIN_APPROX_SIMPLE

        contours,_ = cv2.findContours(thresh, mode, method)
        return cv2.drawContours(image, contours, -1, color, thickness)
