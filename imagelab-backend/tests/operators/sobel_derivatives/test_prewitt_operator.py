import numpy as np
import pytest

from app.operators.registry import get_operator
from app.operators.sobel_derivatives.prewitt_operator import PrewittOperator


def _vertical_edge_image() -> np.ndarray:
    """20x20 grayscale image: left half black, right half white."""
    img = np.zeros((20, 20), dtype=np.uint8)
    img[:, 10:] = 255
    return img


def test_block_is_registered():
    assert get_operator("sobelderivatives_prewittoperator") is PrewittOperator


@pytest.mark.parametrize("shape", [(20, 30), (20, 30, 1), (20, 30, 3), (20, 30, 4)])
def test_output_is_2d_uint8_for_every_supported_shape(shape):
    image = np.zeros(shape, dtype=np.uint8)
    result = PrewittOperator({}).compute(image)
    assert result.shape == (20, 30)
    assert result.dtype == np.uint8


def test_flat_image_has_no_edges():
    image = np.full((20, 20), 128, dtype=np.uint8)
    result = PrewittOperator({}).compute(image)
    assert (result == 0).all()


def test_vertical_edge_is_detected():
    result = PrewittOperator({}).compute(_vertical_edge_image())
    assert (result[:, 9:11] == 255).all()
    assert (result[:, :8] == 0).all()
    assert (result[:, 12:] == 0).all()


def test_horizontal_edge_is_detected():
    image = _vertical_edge_image().T.copy()
    result = PrewittOperator({}).compute(image)
    assert (result[9:11, :] == 255).all()
    assert (result[:8, :] == 0).all()
    assert (result[12:, :] == 0).all()


def test_colour_edge_matches_gray_edge():
    gray = _vertical_edge_image()
    bgr = np.stack([gray, gray, gray], axis=2)
    np.testing.assert_array_equal(PrewittOperator({}).compute(bgr), PrewittOperator({}).compute(gray))


def test_rejects_non_uint8_image():
    with pytest.raises(ValueError, match="expects a uint8 image"):
        PrewittOperator({}).compute(np.zeros((10, 10), dtype=np.float32))


def test_rejects_unsupported_channel_count():
    with pytest.raises(ValueError, match="expects 1, 3, or 4 channels"):
        PrewittOperator({}).compute(np.zeros((10, 10, 2), dtype=np.uint8))


def test_rejects_wrong_number_of_dimensions():
    with pytest.raises(ValueError, match="expects a 2-D or 3-D array"):
        PrewittOperator({}).compute(np.zeros((2, 10, 10, 3), dtype=np.uint8))
