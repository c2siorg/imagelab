import cv2
import numpy as np

from app.operators.base import BaseOperator


class AffineImage(BaseOperator):
    """
    Applies an affine transformation to an image.
    
    Allows configurable scaling, shearing, and translation.
    """
    def compute(self, image: np.ndarray) -> np.ndarray:
        rows, cols = image.shape[:2]

        scale_x = float(self.params.get("scale_x", 1.0))
        scale_y = float(self.params.get("scale_y", 1.0))
        shear_x = float(self.params.get("shear_x", 0.0))
        shear_y = float(self.params.get("shear_y", 0.0))
        translate_x = float(self.params.get("translate_x", 0.0))
        translate_y = float(self.params.get("translate_y", 0.0))

        # Affine matrix M = [ [s_x, sh_x, t_x], [sh_y, s_y, t_y] ]
        M = np.float32([
            [scale_x, shear_x, translate_x],
            [shear_y, scale_y, translate_y]
        ])

        return cv2.warpAffine(image, M, (cols, rows))

