import cv2
import numpy as np

from app.operators.base import BaseOperator


class AffineImage(BaseOperator):
    """
    Applies an affine transformation to an image.

    Allows configurable scaling, shearing, translation, and output canvas size.
    The affine matrix is constructed from the following parameters:
      - ``scale_x``, ``scale_y``  — scaling factors (default 1.0)
      - ``shear_x``, ``shear_y``  — shear factors (default 0.0)
      - ``translate_x``, ``translate_y`` — translation in pixels (default 0.0)
      - ``output_width``, ``output_height`` — canvas size of the output image;
        defaults to the original image dimensions (Issue #43 fix).
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        rows, cols = image.shape[:2]

        scale_x = float(self.params.get("scale_x", 1.0))
        scale_y = float(self.params.get("scale_y", 1.0))
        shear_x = float(self.params.get("shear_x", 0.0))
        shear_y = float(self.params.get("shear_y", 0.0))
        translate_x = float(self.params.get("translate_x", 0.0))
        translate_y = float(self.params.get("translate_y", 0.0))

        # Issue #43: output canvas size is now configurable (fixes hardcoded (cols, rows))
        output_width = int(self.params.get("output_width", cols))
        output_height = int(self.params.get("output_height", rows))

        # Affine matrix M = [ [s_x, sh_x, t_x], [sh_y, s_y, t_y] ]
        M = np.float32([
            [scale_x, shear_x, translate_x],
            [shear_y, scale_y, translate_y]
        ])

        return cv2.warpAffine(image, M, (output_width, output_height))
