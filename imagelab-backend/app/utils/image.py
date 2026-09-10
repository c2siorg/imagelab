import base64

import cv2
import numpy as np


def decode_base64_image(b64: str) -> np.ndarray:
    data = base64.b64decode(b64)
    arr = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("Could not decode image data")
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
