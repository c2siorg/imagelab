import cv2
import numpy as np
import pytest

from app.operators.sobel_derivatives.roberts_operator import RobertsOperator


def _diagonal_edge_image() -> np.ndarray:
    """100x100 grayscale image with a diagonal edge running through the centre."""
    img = np.zeros((100, 100), dtype=np.uint8)
    np.fill_diagonal(img[20:80, 20:80], 255)
    return img


def test_roberts_returns_uint8() -> None:
    result = RobertsOperator({}).compute(_diagonal_edge_image())
    assert result.dtype == np.uint8


def test_roberts_output_shape_matches_input() -> None:
    img = _diagonal_edge_image()
    result = RobertsOperator({}).compute(img)
    assert result.shape == img.shape


def test_roberts_output_is_png_encodable() -> None:
    result = RobertsOperator({}).compute(_diagonal_edge_image())
    success, _ = cv2.imencode(".png", result)
    assert success, "Roberts output must be PNG-encodable"


def test_roberts_rejects_non_uint8() -> None:
    with pytest.raises(ValueError, match="expects a uint8 image"):
        RobertsOperator({}).compute(np.zeros((10, 10), dtype=np.float32))


def test_roberts_rejects_unsupported_channel_count() -> None:
    img = np.zeros((10, 10, 2), dtype=np.uint8)
    with pytest.raises(ValueError, match="expects 1, 3, or 4 channels"):
        RobertsOperator({}).compute(img)


def test_roberts_rejects_wrong_dimensionality() -> None:
    img = np.zeros((2, 10, 10, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="expects a 2-D or 3-D array"):
        RobertsOperator({}).compute(img)


def test_roberts_detects_a_strong_diagonal_edge() -> None:
    """A hard diagonal step must produce a strong response, not a near-zero one."""
    result = RobertsOperator({}).compute(_diagonal_edge_image())
    assert result.max() > 200, f"Expected strong edge response, got max={result.max()}"


def test_roberts_is_silent_on_a_uniform_image() -> None:
    """No gradient means no edges; this guards against a constant-offset kernel bug."""
    result = RobertsOperator({}).compute(np.full((32, 32), 128, dtype=np.uint8))
    assert result.max() == 0, f"Expected no response on a uniform image, got max={result.max()}"


def test_roberts_responds_at_the_boundary_and_stays_flat_elsewhere() -> None:
    """With only the bottom-right quadrant of an 8x8 image raised, only the quadrant boundary should respond.

    This pins the defining behaviour of the Roberts Cross kernels: they compare the two
    diagonals of each 2x2 window, so the interior of each uniform region produces nothing.
    The response is confined to row 4 and column 4 — the two legs of the quadrant boundary.
    """
    img = np.zeros((8, 8), dtype=np.uint8)
    img[4:, 4:] = 255

    result = RobertsOperator({}).compute(img)

    assert result[0:4, 0:4].max() == 0, "Top-left quadrant must stay flat"
    assert result[5:, 5:].max() == 0, "Bottom-right quadrant interior must stay flat"
    assert result[0:4, 5:].max() == 0, "Top-right region must stay flat"
    assert result[5:, 0:4].max() == 0, "Bottom-left region must stay flat"

    assert np.count_nonzero(result) == 7, "Response must be confined to the boundary row and column"
    assert result[4, 4] == 255
    assert result[4, 7] == 255
    assert result[7, 4] == 255


def test_roberts_uses_the_euclidean_norm_of_both_kernels() -> None:
    """A contrast-100 axis-aligned step peaks at 100 * sqrt(2) ~= 141.4.

    This discriminates the L2 magnitude of BOTH kernels from the two plausible wrong
    implementations: an L1 sum (|Gx| + |Gy| = 200) and a single-kernel gradient (= 100).
    Both saturate to the same clipped 255 as the correct answer when contrast is 255, so
    the fixture deliberately uses a mid-tone contrast.
    """
    img = np.zeros((32, 32), dtype=np.uint8)
    img[:, 16:] = 100

    result = RobertsOperator({}).compute(img)

    assert result.max() == pytest.approx(100 * np.sqrt(2), abs=1)


def test_roberts_saturates_a_full_contrast_step_instead_of_wrapping() -> None:
    """A 0 -> 255 step has true magnitude 255 * sqrt(2) ~= 360.6.

    Without the clip, astype(uint8) would wrap 360 to 104, so the brightest edge in the
    image would render dark. This is the most user-visible line in the operator.
    """
    img = np.zeros((9, 9), dtype=np.uint8)
    img[:, 4:] = 255

    result = RobertsOperator({}).compute(img)

    assert result[4, 4] == 255, f"expected saturation at 255, got {result[4, 4]} (uint8 wrap would be 104)"


@pytest.mark.parametrize("shape", [(32, 32, 3), (32, 32, 4)])
def test_roberts_converts_colour_input_with_bgr_luma_weighting(shape: tuple[int, ...]) -> None:
    """Grayscale must be a real luma conversion, not a read of a single channel.

    Pure red is (B=0, G=0, R=255) in BGR order, so channel 0 is 0 while the luma is
    0.299 * 255 ~= 76. Reading channel 0 would blank the image entirely.
    """
    img = np.zeros((32, 32, shape[2]), dtype=np.uint8)
    img[:, 16:, 2] = 255

    result = RobertsOperator({}).compute(img)

    assert result.max() > 0, "colour input must not be read from a single channel"
    assert result.max() == pytest.approx(0.299 * 255 * np.sqrt(2), abs=2)


def test_roberts_is_invariant_to_a_uniform_brightness_offset() -> None:
    """An edge detector must respond to contrast, not absolute brightness."""
    rng = np.random.default_rng(7)
    base = rng.integers(20, 120, size=(24, 24), dtype=np.uint8)
    brightened = np.clip(base.astype(np.int16) + 30, 0, 255).astype(np.uint8)

    np.testing.assert_allclose(
        RobertsOperator({}).compute(base),
        RobertsOperator({}).compute(brightened),
        atol=1,
        rtol=0,
    )


@pytest.mark.parametrize("shape", [(32, 32), (32, 32, 1), (32, 32, 3), (32, 32, 4)])
def test_roberts_accepts_2d_1_3_and_4_channel_inputs(shape: tuple[int, ...]) -> None:
    img = np.full(shape, 200, dtype=np.uint8)
    result = RobertsOperator({}).compute(img)
    assert result.shape == shape[:2]
    assert result.dtype == np.uint8
