import cv2
import numpy as np

MAX_DETECTION_DIM = 720


def to_grayscale(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image
    if image.ndim == 3 and image.shape[2] == 1:
        return image[:, :, 0]
    if image.ndim == 3 and image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if image.ndim == 3 and image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    raise ValueError(f"Unsupported image shape {image.shape}.")


def prepare_output(image: np.ndarray) -> tuple[np.ndarray, tuple[int, ...]]:
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), ()
    if image.ndim == 3 and image.shape[2] == 1:
        return cv2.cvtColor(image[:, :, 0], cv2.COLOR_GRAY2BGR), ()
    if image.ndim == 3 and image.shape[2] == 3:
        return image.copy(), ()
    if image.ndim == 3 and image.shape[2] == 4:
        return image.copy(), (255,)
    raise ValueError(f"Unsupported image shape {image.shape}.")


def resize_for_detection(gray: np.ndarray, min_size: int) -> tuple[np.ndarray, float, tuple[int, int]]:
    height, width = gray.shape[:2]
    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid image dimensions {width}x{height}.")

    scale = min(MAX_DETECTION_DIM / max(height, width), 1.0)
    if scale == 1.0:
        return gray, 1.0, (min_size, min_size) if min_size > 0 else (0, 0)

    resized_width = max(1, int(round(width * scale)))
    resized_height = max(1, int(round(height * scale)))
    resized = cv2.resize(gray, (resized_width, resized_height), interpolation=cv2.INTER_AREA)
    scaled_min_size = max(1, int(round(min_size * scale))) if min_size > 0 else 0
    return resized, scale, ((scaled_min_size, scaled_min_size) if scaled_min_size > 0 else (0, 0))
