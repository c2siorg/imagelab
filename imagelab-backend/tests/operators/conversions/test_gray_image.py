import cv2
import numpy as np
import pytest

from app.operators.conversions.gray_image import GrayImage


def test_gray_image_returns_2d_grayscale_input_unchanged() -> None:
    image = np.arange(100, dtype=np.uint8).reshape(10, 10)

    out = GrayImage({}).compute(image)

    assert out.shape == image.shape
    assert np.array_equal(out, image)


def test_gray_image_converts_bgr_to_grayscale() -> None:
    image = np.zeros((6, 6, 3), dtype=np.uint8)
    image[:, :, 0] = 10
    image[:, :, 1] = 20
    image[:, :, 2] = 30

    out = GrayImage({}).compute(image)
    expected = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    assert out.shape == (6, 6)
    assert np.array_equal(out, expected)


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


def test_gray_image_handles_single_channel_3d_input() -> None:
    image = np.arange(64, dtype=np.uint8).reshape(8, 8, 1)

    out = GrayImage({}).compute(image)

    assert out.shape == (8, 8)
    assert np.array_equal(out, image[:, :, 0])


def test_gray_image_rejects_unsupported_channel_count() -> None:
    image = np.zeros((4, 4, 2), dtype=np.uint8)

    with pytest.raises(
        ValueError,
        match="GrayImage expects a 2D grayscale image or a 3D image with 1, 3, or 4 channels",
    ):
        GrayImage({}).compute(image)
