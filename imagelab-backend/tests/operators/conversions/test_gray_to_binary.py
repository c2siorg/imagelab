import numpy as np

from app.operators.conversions.gray_to_binary import GrayToBinary


def test_gray_to_binary_grayscale_input() -> None:
    image = np.array([[50, 150]], dtype=np.uint8)
    out = GrayToBinary({"thresholdValue": 100, "maxValue": 255}).compute(image)
    assert out.shape == (1, 2)
    assert out[0, 0] == 0
    assert out[0, 1] == 255


def test_gray_to_binary_bgr_input_converts_first() -> None:
    image = np.array([[[50, 150, 200]]], dtype=np.uint8)
    out = GrayToBinary({"thresholdValue": 100, "maxValue": 255}).compute(image)
    assert out.ndim == 2, "BGR input must produce a single-channel output"


def test_gray_to_binary_bgra_input_converts_first() -> None:
    image = np.array([[[50, 150, 200, 255]]], dtype=np.uint8)
    out = GrayToBinary({"thresholdValue": 100, "maxValue": 255}).compute(image)
    assert out.ndim == 2, "BGRA input must produce a single-channel output"


def test_gray_to_binary_default_params() -> None:
    image = np.array([[0, 128, 255]], dtype=np.uint8)
    out = GrayToBinary({}).compute(image)
    assert out.ndim == 2
    assert out[0, 0] == 0
    assert out[0, 1] == 255
    assert out[0, 2] == 255
