import cv2
import numpy as np

from app.operators.base import BaseOperator

class ClacheImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        clip_limit = float(self.params.get("clipLimit", 2.0))
        grid_size = (
            int(self.params.get("tileGridSizeX", 8)),
            int(self.params.get("tileGridSizeY", 8))
        )

        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)

        if len(image.shape) == 3:
            # Step 1: BGR -> LAB
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Step 2: Apply to 'L' channel
            l_enhanced = clahe.apply(l)
            
            # Step 3: Merge and BGR back
            enhanced_lab = cv2.merge((l_enhanced, a, b))
            return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        else:
            # Grayscale handling
            return clahe.apply(image)
