import numpy as np

from app.operators.filtering.laplacian import Laplacian


def test_params_attribute_is_set():
    """The base contract: every operator must have self.params after construction."""
    op = Laplacian({"ksize": 3})
    assert op.params == {"ksize": 3}


def test_compute_runs_with_default_ksize():
    image = np.zeros((32, 32, 3), dtype=np.uint8)
    image[8:24, 8:24] = 255
    result = Laplacian({}).compute(image)
    assert result.dtype == np.uint8
    assert result.shape == image.shape[:2]
