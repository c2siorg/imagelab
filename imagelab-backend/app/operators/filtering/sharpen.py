import cv2
import numpy as np

from app.operators.base import BaseOperator


class Sharpen(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        strength = float(self.params.get("strength", 1.0))
        # Clamp strength to [0.0, 2.0]
        strength = max(0.0, min(2.0, strength))
        
        # Convert RGBA to BGR if needed
        if len(image.shape) == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        
        # Standard sharpening kernel
        kernel = np.array([[0, -1, 0],
                          [-1, 5, -1],
                          [0, -1, 0]], dtype=np.float32)
        
        # Apply the sharpening kernel
        sharpened = cv2.filter2D(image, -1, kernel)
        
        # Blend between original and sharpened based on strength
        result = cv2.addWeighted(image, 1.0 - strength, sharpened, strength, 0)
        
        # Ensure output is uint8
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        return result
