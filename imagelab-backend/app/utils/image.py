import base64

import cv2
import numpy as np

from app.exceptions import MemoryLimitExceededException

MAX_IMAGE_MEMORY_BYTES = 50 * 1024 * 1024  # 50 MB default threshold


def decode_base64_image(b64: str) -> np.ndarray:
    data = base64.b64decode(b64)
    arr = np.frombuffer(data, dtype=np.uint8)
    # IMREAD_UNCHANGED ignores the EXIF orientation tag. JPEG has no alpha channel,
    # so for JPEG these flags keep the same pixels and also apply the rotation.
    is_jpeg = data[:2] == b"\xff\xd8"
    flags = cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH if is_jpeg else cv2.IMREAD_UNCHANGED
    image = cv2.imdecode(arr, flags)
    if image is None:
        raise ValueError("Could not decode image data")
    if image.dtype == np.uint16:
        # Operators work on 8-bit images, so scale 16-bit values (0-65535) down to 0-255.
        image = cv2.convertScaleAbs(image, alpha=1 / 257)
    return image


SUPPORTED_FORMATS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif"}
FORMAT_ALIASES = {"jpg": "jpeg", "tif": "tiff"}


def encode_image_base64(image: np.ndarray, fmt: str = "png") -> str:
    fmt = fmt.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported image format: {fmt!r}. Supported: {sorted(SUPPORTED_FORMATS)}")
    ext = FORMAT_ALIASES.get(fmt, fmt)
    success, buf = cv2.imencode(f".{ext}", image)
    if not success:
        raise ValueError(f"Could not encode image as {ext}")
    return base64.b64encode(buf).decode("utf-8")


def check_output_memory(image: np.ndarray, width: int, height: int, max_bytes: int = MAX_IMAGE_MEMORY_BYTES) -> None:
    """Reject an output of ``width`` x ``height`` (same channels and dtype as ``image``) before it is allocated."""
    channels = image.shape[2] if image.ndim == 3 else 1
    nbytes = int(width) * int(height) * channels * image.itemsize
    if nbytes > max_bytes:
        raise MemoryLimitExceededException(
            f"Image memory footprint ({nbytes} bytes) exceeds memory limit threshold of {max_bytes} bytes."
        )
