import cv2
import numpy as np

from app.operators.base import BaseOperator


class AffineImage(BaseOperator):
    """
    Applies an affine transformation to an image.

    Allows configurable scaling, shearing, translation, and output canvas size.
    The affine matrix is constructed from the following parameters:
      - ``scale_x``, ``scale_y`` (float): Scaling factors (0.01 to 10.0, default 1.0).
      - ``shear_x``, ``shear_y`` (float): Shear factors (-2.0 to 2.0, default 0.0).
      - ``translate_x``, ``translate_y`` (float): Translation in pixels (default 0.0).
      - ``output_width``, ``output_height`` (int): Canvas size (max 5000, default original dims).
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None:
            raise ValueError("Input image cannot be None")

        rows, cols = image.shape[:2]

        scale_x = float(self.params.get("scale_x", 1.0))
        scale_y = float(self.params.get("scale_y", 1.0))
        shear_x = float(self.params.get("shear_x", 0.0))
        shear_y = float(self.params.get("shear_y", 0.0))
        translate_x = float(self.params.get("translate_x", 0.0))
        translate_y = float(self.params.get("translate_y", 0.0))

        if not (0.01 <= scale_x <= 10.0 and 0.01 <= scale_y <= 10.0):
            raise ValueError("Scale factors must be between 0.01 and 10.0")
        
        if not (-2.0 <= shear_x <= 2.0 and -2.0 <= shear_y <= 2.0):
            raise ValueError("Shear factors must be between -2.0 and 2.0")

        # Issue #43: output canvas size is now configurable
        output_width = int(self.params.get("output_width", cols))
        output_height = int(self.params.get("output_height", rows))

        if not (1 <= output_width <= 5000 and 1 <= output_height <= 5000):
            raise ValueError("Output dimensions must be between 1 and 5000")

        # Affine matrix M = [ [s_x, sh_x, t_x], [sh_y, s_y, t_y] ]
        M = np.array([
            [scale_x, shear_x, translate_x],
            [shear_y, scale_y, translate_y]
        ], dtype=np.float32)

        return cv2.warpAffine(image, M, (output_width, output_height))
