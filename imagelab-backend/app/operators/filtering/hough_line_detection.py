import cv2
import numpy as np

from app.operators.base import BaseOperator


class HoughLineDetection(BaseOperator):
    """
    Detects lines in an image using the Probabilistic Hough Line Transform.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        """
        Apply Hough Line Detection.

        Args:
            image: A uint8 NumPy array of shape (H, W), (H, W, 3) or (H, W, 4).

        Returns:
            The image with detected lines drawn. If BGRA, returns BGR.
        """
        if image is None:
            raise ValueError("Input image cannot be None")
        if image.dtype != np.uint8:
            raise ValueError("Hough Line Detection requires a uint8 image.")

        canny_threshold1 = int(self.params.get("canny_threshold1", 50))
        canny_threshold2 = int(self.params.get("canny_threshold2", 150))
        rho = float(self.params.get("rho", 1.0))
        theta_degrees = float(self.params.get("theta_degrees", 1.0))
        threshold = int(self.params.get("threshold", 100))
        min_line_length = int(self.params.get("min_line_length", 50))
        max_line_gap = int(self.params.get("max_line_gap", 10))
        line_color = list(self.params.get("line_color", [0, 255, 0]))
        thickness = int(self.params.get("thickness", 2))

        if thickness <= 0:
            raise ValueError(f"thickness must be > 0, got {thickness}")

        # Handle color and alpha
        if len(image.shape) == 3:
            if image.shape[2] == 4:
                # Strip alpha
                processing_img = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            else:
                processing_img = image.copy()
        else:
            processing_img = image.copy()

        # Convert to grayscale for Canny
        if len(processing_img.shape) == 3:
            gray = cv2.cvtColor(processing_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = processing_img

        # Canny edge detection
        edges = cv2.Canny(gray, canny_threshold1, canny_threshold2)

        # Hough Line Detection
        theta = np.pi * theta_degrees / 180.0
        lines = cv2.HoughLinesP(
            edges, rho, theta, threshold, minLineLength=min_line_length, maxLineGap=max_line_gap
        )

        # Draw lines on a copy of the original (or BGR version)
        result = processing_img.copy()
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(result, (x1, y1), (x2, y2), tuple(line_color), thickness)

        return result
