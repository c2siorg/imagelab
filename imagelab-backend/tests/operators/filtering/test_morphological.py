import numpy as np
import pytest

from app.operators.filtering.morphological import Morphological


def test_morphological_default_kernel_matches_explicit_5() -> None:
    image = np.zeros((30, 30), dtype=np.uint8)
    image[8:22, 8:22] = 255

    out_default = Morphological({"type": "OPEN"}).compute(image)
    out_explicit = Morphological({"type": "OPEN", "kernelSize": 5}).compute(image)

    assert np.array_equal(out_default, out_explicit)


@pytest.mark.parametrize("kernel_size", [0, -1, 2, 8, "abc", 3.5, True, False, None, 4.0])
def test_morphological_rejects_invalid_kernel_sizes(kernel_size: object) -> None:
    with pytest.raises(ValueError, match="kernelSize"):
        Morphological({"type": "OPEN", "kernelSize": kernel_size})


def test_morphological_accepts_positive_odd_kernel_sizes() -> None:
    image = np.zeros((25, 25), dtype=np.uint8)
    image[5:20, 5:20] = 255

    out_3 = Morphological({"type": "CLOSE", "kernelSize": 3}).compute(image)
    out_7 = Morphological({"type": "CLOSE", "kernelSize": 7}).compute(image)

    assert out_3.shape == image.shape
    assert out_7.shape == image.shape
    # A larger kernel closes more aggressively — produces a more dilated result
    assert int(out_7.sum()) >= int(out_3.sum())


def test_morphological_kernel_size_changes_result() -> None:
    image = np.zeros((40, 40), dtype=np.uint8)
    image[2:7, 2:7] = 255
    image[10:30, 10:30] = 255

    out_small = Morphological({"type": "OPEN", "kernelSize": 3}).compute(image)
    out_large = Morphological({"type": "OPEN", "kernelSize": 15}).compute(image)

    assert not np.array_equal(out_small, out_large)
    assert int(out_small.sum()) > int(out_large.sum())


def test_morphological_top_hat_converts_rgba_to_rgb() -> None:
    image = np.zeros((20, 20, 4), dtype=np.uint8)
    image[6:14, 6:14] = [255, 255, 255, 255]

    out = Morphological({"type": "TOPHAT", "kernelSize": 5}).compute(image)

    assert out.shape == (20, 20, 3)


def test_morphological_accepts_kernel_size_1() -> None:
    image = np.zeros((20, 20), dtype=np.uint8)
    out = Morphological({"type": "OPEN", "kernelSize": 1}).compute(image)
    assert out.shape == image.shape


def test_morphological_kernel_larger_than_image_does_not_crash() -> None:
    image = np.zeros((20, 20), dtype=np.uint8)
    image[5:15, 5:15] = 255

    out = Morphological({"type": "OPEN", "kernelSize": 21}).compute(image)

    assert out.shape == image.shape
