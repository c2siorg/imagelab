import cv2
import numpy as np
import pytest

from app.operators.conversions.gray_image import GrayImage


def test_gray_image_returns_2d_grayscale_input_unchanged() -> None:
    image = np.arange(100, dtype=np.uint8).reshape(10, 10)

    out = GrayImage({}).compute(image)

    assert out.shape == image.shape
    assert np.array_equal(out, image)
    assert out is not image, "compute() must return a copy, not the original array"
    # Verify no aliasing:
    out[0, 0] = 255
    assert image[0, 0] != 255, "Mutating output must not affect input"


def test_gray_image_converts_bgr_to_grayscale() -> None:
    image = np.zeros((6, 6, 3), dtype=np.uint8)
    image[:, :, 0] = 10
    image[:, :, 1] = 20
    image[:, :, 2] = 30

    out = GrayImage({}).compute(image)
    expected = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    assert out.shape == (6, 6)
    assert np.array_equal(out, expected)
    # B=10, G=20, R=30: Y ≈ 22 (OpenCV integer approximation)
    assert int(out[0, 0]) == int(expected[0, 0])
    assert int(out[0, 0]) == 22


def test_gray_image_converts_bgra_to_grayscale() -> None:
    image = np.zeros((6, 6, 4), dtype=np.uint8)
    image[:, :, 0] = 10
    image[:, :, 1] = 20
    image[:, :, 2] = 30
    image[:, :, 3] = 255

    out = GrayImage({}).compute(image)
    expected = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)

    assert out.shape == (6, 6)
    assert np.array_equal(out, expected)
    # B=10, G=20, R=30: Y ≈ 22 (OpenCV integer approximation)
    assert int(out[0, 0]) == int(expected[0, 0])
    assert int(out[0, 0]) == 22


def test_gray_image_handles_single_channel_3d_input() -> None:
    image = np.arange(64, dtype=np.uint8).reshape(8, 8, 1)

    out = GrayImage({}).compute(image)

    assert out.shape == (8, 8)
    assert np.array_equal(out, image[:, :, 0])
    assert out is not image[:, :, 0], "compute() must return a copy"
    # Verify no aliasing:
    out[0, 0] = 255
    assert image[0, 0, 0] != 255, "Mutating output must not affect input"


@pytest.mark.parametrize(
    "shape",
    [
        (10,),  # 1-D flat array
        (4, 4, 2),  # 3-D, 2-channel
        (4, 4, 5),  # 3-D, 5-channel
        (2, 4, 4, 3),  # 4-D batch
    ],
)
def test_gray_image_rejects_unsupported_shapes(shape: tuple) -> None:
    image = np.zeros(shape, dtype=np.uint8)

    with pytest.raises(ValueError, match=r"GrayImage expects"):
        GrayImage({}).compute(image)
