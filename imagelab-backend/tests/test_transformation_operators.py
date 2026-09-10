import numpy as np
import pytest

from app.operators.transformation.distance_transform import DistanceTransform
from app.operators.transformation.laplacian import Laplacian


@pytest.fixture
def color_image():
    rng = np.random.default_rng(seed=42)
    return rng.integers(0, 256, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def grayscale_image():
    rng = np.random.default_rng(seed=42)
    return rng.integers(0, 256, (100, 100), dtype=np.uint8)


@pytest.fixture
def binary_image():
    img = np.zeros((100, 100), dtype=np.uint8)
    img[20:80, 20:80] = 255
    return img


@pytest.fixture
def binary_color_image():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[20:80, 20:80] = 255
    return img


class TestDistanceTransform:
    def test_default_params_output_shape(self, binary_color_image):
        result = DistanceTransform({}).compute(binary_color_image)
        assert result.shape == (100, 100)

    def test_output_is_uint8(self, binary_color_image):
        result = DistanceTransform({}).compute(binary_color_image)
        assert result.dtype == np.uint8

    def test_output_normalized_to_0_255(self, binary_color_image):
        result = DistanceTransform({}).compute(binary_color_image)
        assert result.min() >= 0
        assert result.max() <= 255

    def test_grayscale_input_accepted(self, binary_image):
        result = DistanceTransform({}).compute(binary_image)
        assert result.dtype == np.uint8
        assert result.shape == (100, 100)

    def test_blank_image_returns_all_zeros(self):
        blank = np.zeros((50, 50, 3), dtype=np.uint8)
        result = DistanceTransform({}).compute(blank)
        assert result.max() == 0

    def test_fully_white_image_does_not_crash(self):
        """Ensures the operator handles all-foreground input gracefully."""
        white = np.full((50, 50, 3), 255, dtype=np.uint8)
        result = DistanceTransform({}).compute(white)
        assert result.dtype == np.uint8
        assert result.shape == (50, 50)

    @pytest.mark.parametrize("dist_type", ["DIST_C", "DIST_L1", "DIST_L2"])
    def test_distance_type_produces_valid_output(self, binary_color_image, dist_type):
        result = DistanceTransform({"type": dist_type}).compute(binary_color_image)
        assert result.dtype == np.uint8
        assert result.shape == (100, 100)
        assert result.min() >= 0
        assert result.max() <= 255

    def test_unknown_type_does_not_raise(self, binary_color_image):
        """Operator should handle unrecognised type strings gracefully."""
        result = DistanceTransform({"type": "INVALID"}).compute(binary_color_image)
        assert result.dtype == np.uint8
        assert result.shape == (100, 100)

    def test_does_not_mutate_input(self, binary_color_image):
        original = binary_color_image.copy()
        DistanceTransform({}).compute(binary_color_image)
        np.testing.assert_array_equal(binary_color_image, original)

    def test_interior_pixels_have_higher_distance_than_border(self, binary_color_image):
        # binary_color_image has foreground region rows 20-79, cols 20-79.
        # Row 20 is the boundary; row 50 is the centre.
        result = DistanceTransform({"type": "DIST_L2"}).compute(binary_color_image)
        centre_val = int(result[50, 50])  # deep interior — maximal distance
        edge_val = int(result[20, 50])  # boundary pixel — distance is 0 or minimal
        assert centre_val > edge_val

    def test_output_shape_matches_for_non_square_image(self):
        img = np.zeros((60, 120, 3), dtype=np.uint8)
        img[10:50, 10:110] = 255
        result = DistanceTransform({}).compute(img)
        assert result.shape == (60, 120)


class TestLaplacian:
    def test_default_params_output_shape(self, color_image):
        result = Laplacian({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = Laplacian({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_grayscale_input_accepted(self, grayscale_image):
        result = Laplacian({}).compute(grayscale_image)
        assert result.dtype == np.uint8
        assert result.shape == grayscale_image.shape

    def test_uniform_image_produces_zero_output(self):
        uniform = np.full((50, 50, 3), 128, dtype=np.uint8)
        result = Laplacian({}).compute(uniform)
        assert result.max() == 0

    def test_edge_pixels_have_high_response(self):
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[30:70, 30:70] = 255
        result = Laplacian({}).compute(img)
        edge_response = int(result[30, 50].mean())
        interior_response = int(result[50, 50].mean())
        assert edge_response > interior_response, (
            f"Expected edge response ({edge_response}) > interior ({interior_response})"
        )

    def test_output_values_in_valid_uint8_range(self, color_image):
        result = Laplacian({}).compute(color_image)
        assert result.min() >= 0
        assert result.max() <= 255

    def test_does_not_mutate_input(self, color_image):
        original = color_image.copy()
        Laplacian({}).compute(color_image)
        np.testing.assert_array_equal(color_image, original)

    def test_output_shape_matches_input_for_non_square_image(self):
        rng = np.random.default_rng(seed=42)
        img = rng.integers(0, 256, (60, 120, 3), dtype=np.uint8)
        result = Laplacian({}).compute(img)
        assert result.shape == img.shape
