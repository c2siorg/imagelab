import numpy as np

from app.operators.transformation.laplacian import Laplacian

# Black image with a bright white square – creates strong edges for Laplacian.
_IMG = np.zeros((64, 64), dtype=np.uint8)
_IMG[16:48, 16:48] = 255


class TestLaplacian:
    def test_output_dtype_and_range(self):
        result = Laplacian({}).compute(_IMG)
        assert result.dtype == np.uint8
        assert result.min() >= 0 and result.max() <= 255

    def test_no_uint8_wrap_around(self):
        result = Laplacian({}).compute(_IMG)
        # Edge pixels must be bright, not dark from modulo wrapping.
        edge_value = result[16, 32]
        interior_value = result[32, 32]
        assert edge_value > interior_value

    def test_ksize_3(self):
        result = Laplacian({"ksize": 3}).compute(_IMG)
        assert result.dtype == np.uint8
        assert result.max() <= 255
