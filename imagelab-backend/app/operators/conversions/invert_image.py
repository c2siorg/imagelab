import cv2
import numpy as np

from app.operators.base import BaseOperator


class InvertImage(BaseOperator):
    """Inverts all pixel values using bitwise NOT (equivalent to 255 - value for uint8)."""

    def compute(self, image: np.ndarray) -> np.ndarray:
        """
        Apply bitwise inversion to the image.

        For RGBA images, only the BGR channels are inverted; the alpha
        channel is preserved unchanged. Float images are not supported.

        Args:
            image: A uint8 ndarray with shape (H, W) or (H, W, 3/4).

        Returns:
            Inverted image with the same shape and dtype as the input.
        """
        if image is None or not isinstance(image, np.ndarray):
            raise TypeError(f"InvertImage.compute expects an np.ndarray, got {type(image).__name__}")
        if image.ndim not in (2, 3):
            raise ValueError(f"InvertImage.compute expects a 2-D or 3-D array, got shape {image.shape}")
        if image.dtype.kind == "f":
            raise ValueError(
                f"InvertImage does not support float images (dtype={image.dtype}). Convert to uint8 first."
            )

        if len(image.shape) == 3 and image.shape[2] == 4:
            bgr = image[:, :, :3]
            alpha = image[:, :, 3:4]
            return np.concatenate([cv2.bitwise_not(bgr), alpha], axis=2)

        return cv2.bitwise_not(image)
