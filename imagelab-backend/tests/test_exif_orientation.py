import base64
import struct

import cv2
import numpy as np
import pytest

from app.utils.image import decode_base64_image

# How the stored image must be transformed to display it for each EXIF orientation value.
EXPECTED = {
    1: lambda a: a,
    2: lambda a: np.fliplr(a),
    3: lambda a: np.rot90(a, 2),
    4: lambda a: np.flipud(a),
    5: lambda a: np.swapaxes(a, 0, 1),
    6: lambda a: np.rot90(a, -1),
    7: lambda a: np.rot90(np.swapaxes(a, 0, 1), 2),
    8: lambda a: np.rot90(a, 1),
}


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def _jpeg_with_orientation(image: np.ndarray, orientation: int) -> bytes:
    jpeg = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 100])[1].tobytes()
    ifd = b"\x00\x01" + struct.pack(">HHIHH", 0x0112, 3, 1, orientation, 0) + b"\x00\x00\x00\x00"
    exif = b"Exif\x00\x00MM\x00\x2a\x00\x00\x00\x08" + ifd
    return jpeg[:2] + b"\xff\xe1" + struct.pack(">H", len(exif) + 2) + exif + jpeg[2:]


@pytest.fixture
def image() -> np.ndarray:
    # 16 rows x 32 columns with a different grey level in each quarter
    img = np.zeros((16, 32, 3), dtype=np.uint8)
    img[:8, :16] = 255
    img[:8, 16:] = 170
    img[8:, :16] = 85
    return img


@pytest.mark.parametrize("orientation", range(1, 9))
def test_jpeg_is_rotated_like_a_browser_shows_it(image, orientation):
    decoded = decode_base64_image(_b64(_jpeg_with_orientation(image, orientation)))
    expected = EXPECTED[orientation](image)
    assert decoded.shape == expected.shape
    np.testing.assert_allclose(decoded.astype(int), expected.astype(int), atol=12)


def test_jpeg_without_exif_is_unchanged(image):
    decoded = decode_base64_image(_b64(cv2.imencode(".jpg", image)[1].tobytes()))
    assert decoded.shape == image.shape


def test_grayscale_jpeg_stays_single_channel(image):
    decoded = decode_base64_image(_b64(cv2.imencode(".jpg", image[:, :, 0])[1].tobytes()))
    assert decoded.ndim == 2


def test_png_keeps_alpha_channel(image):
    bgra = np.dstack([image, np.full(image.shape[:2], 200, dtype=np.uint8)])
    decoded = decode_base64_image(_b64(cv2.imencode(".png", bgra)[1].tobytes()))
    assert decoded.shape == (16, 32, 4)
