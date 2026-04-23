import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


class HoughLines(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        rho = float(self.params.get("rho", 1.0))
        theta_degrees = float(self.params.get("thetaDegrees", 1.0))
        theta = float(np.deg2rad(theta_degrees))
        threshold_val = int(self.params.get("threshold", 50))
        min_line_length = int(self.params.get("minLineLength", 50))
        max_line_gap = int(self.params.get("maxLineGap", 10))
        color_hex = self.params.get("color", "#00FF00")
        thickness = int(self.params.get("thickness", 2))

        if rho <= 0:
            raise ValueError(f"'rho' must be > 0, got {rho}")
        if theta_degrees <= 0:
            raise ValueError(f"'thetaDegrees' must be > 0, got {theta_degrees}")
        if thickness < 1:
            raise ValueError(f"'thickness' must be >= 1, got {thickness}")

        bgr_color = hex_to_bgr(color_hex)

        if len(image.shape) == 3:
            if image.shape[2] == 4:
                gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            else:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        canny_low = float(self.params.get("cannyThreshold1", 50))
        canny_high = float(self.params.get("cannyThreshold2", 150))
        aperture = int(self.params.get("cannyApertureSize", 3))

        edges = cv2.Canny(gray, canny_low, canny_high, apertureSize=aperture)

        lines = cv2.HoughLinesP(
            edges,
            rho=rho,
            theta=theta,
            threshold=threshold_val,
            minLineLength=min_line_length,
            maxLineGap=max_line_gap,
        )

        if len(image.shape) == 2:
            output_base = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:
            output_base = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        else:
            output_base = image.copy()

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(output_base, (x1, y1), (x2, y2), bgr_color, thickness)

        return output_base
