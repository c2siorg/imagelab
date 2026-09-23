import numpy as np

from app.operators.base import BaseOperator


class CropImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        height, width = image.shape[:2]

        # Get cropping coordinates from parameters with defaults
        x1 = int(self.params.get("x1", 0))
        y1 = int(self.params.get("y1", 0))
        x2 = int(self.params.get("x2", width))
        y2 = int(self.params.get("y2", height))

        # Clamp to boundaries (Requirement: No out-of-bounds)
        left = max(0, min(x1, width))
        top = max(0, min(y1, height))
        right = max(0, min(x2, width))
        bottom = max(0, min(y2, height))

        # An empty or inverted rectangle is a user error; raise so the pipeline
        # reports it instead of silently returning the input image.
        if left >= right or top >= bottom:
            raise ValueError(
                f"CropImage: crop rectangle x1={x1}, y1={y1}, x2={x2}, y2={y2} is empty "
                f"for a {width}x{height} image. x1/y1 is the top-left corner and x2/y2 the "
                "bottom-right corner in pixels; x2 must be greater than x1 and y2 greater than y1."
            )

        # Image slicing in OpenCV is image[y1:y2, x1:x2]
        return image[top:bottom, left:right]
