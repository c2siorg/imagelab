import numpy as np

from app.operators.base import BaseOperator
from app.operators.conversions.gray_image import GrayImage


class BitPlaneSlicing(BaseOperator):
    """Shows a single bit plane of the image as a black and white image."""

    def compute(self, image: np.ndarray) -> np.ndarray:
        """
        Extract one bit plane from the image.

        BGR and BGRA images are converted to grayscale first (alpha is ignored).
        Each pixel of the result is 255 where the selected bit is 1 and 0 where
        it is 0, so the plane is visible on screen.

        Params:
            bit: Which bit to show, 0 (least significant) to 7 (most significant).
                Defaults to 7.

        Args:
            image: A uint8 ndarray with shape (H, W) or (H, W, 1/3/4).

        Returns:
            A uint8 (H, W) image containing only 0 and 255.

        Raises:
            ValueError: If bit is outside 0-7 or the image is not uint8.
        """
        bit = int(self.params.get("bit", 7))
        if not 0 <= bit <= 7:
            raise ValueError(f"'bit' must be between 0 and 7, got {bit}.")
        if image.dtype != np.uint8:
            raise ValueError(f"BitPlaneSlicing expects a uint8 image, got dtype={image.dtype}.")

        gray = GrayImage({}).compute(image)
        return ((gray >> bit) & 1).astype(np.uint8) * 255
