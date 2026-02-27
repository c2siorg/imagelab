import pytest

from app.operators.blurring.validation import (
    validate_median_kernel_size,
    validate_positive_kernel_dim,
    validate_positive_odd_kernel_size,
)


class TestValidatePositiveKernelDim:
    """validate_positive_kernel_dim — used by the plain Blur operator."""

    @pytest.mark.parametrize("value", [1, 2, 3, 10, 100])
    def test_valid_positive_values(self, value):
        # Should not raise for any positive integer
        validate_positive_kernel_dim(value, "widthSize")

    @pytest.mark.parametrize("value", [0, -1, -5, -100])
    def test_invalid_non_positive_values(self, value):
        with pytest.raises(ValueError, match="'widthSize'"):
            validate_positive_kernel_dim(value, "widthSize")

    def test_error_message_mentions_name(self):
        with pytest.raises(ValueError, match="'heightSize'"):
            validate_positive_kernel_dim(0, "heightSize")

    def test_error_message_contains_bad_value(self):
        with pytest.raises(ValueError, match="-3"):
            validate_positive_kernel_dim(-3, "widthSize")


class TestValidatePositiveOddKernelSize:
    """validate_positive_odd_kernel_size — used by GaussianBlur."""

    @pytest.mark.parametrize("value", [1, 3, 5, 7, 9, 101])
    def test_valid_positive_odd_values(self, value):
        validate_positive_odd_kernel_size(value, "widthSize")

    @pytest.mark.parametrize("value", [2, 4, 6, 100])
    def test_invalid_even_values(self, value):
        with pytest.raises(ValueError, match="even"):
            validate_positive_odd_kernel_size(value, "widthSize")

    @pytest.mark.parametrize("value", [0, -1, -3])
    def test_invalid_non_positive_values(self, value):
        with pytest.raises(ValueError, match="'widthSize'"):
            validate_positive_odd_kernel_size(value, "widthSize")

    def test_even_error_suggests_neighbours(self):
        with pytest.raises(ValueError, match="3|5"):
            validate_positive_odd_kernel_size(4, "widthSize")

    def test_error_message_mentions_name(self):
        with pytest.raises(ValueError, match="'heightSize'"):
            validate_positive_odd_kernel_size(2, "heightSize")


class TestValidateMedianKernelSize:
    """validate_median_kernel_size — used by MedianBlur."""

    @pytest.mark.parametrize("value", [3, 5, 7, 9, 101])
    def test_valid_odd_values_greater_than_one(self, value):
        validate_median_kernel_size(value, "kernelSize")

    @pytest.mark.parametrize("value", [4, 6, 8, 100])
    def test_invalid_even_values(self, value):
        with pytest.raises(ValueError, match="even"):
            validate_median_kernel_size(value, "kernelSize")

    @pytest.mark.parametrize("value", [1, 0, -1, -5])
    def test_invalid_values_not_greater_than_one(self, value):
        with pytest.raises(ValueError, match="greater than 1"):
            validate_median_kernel_size(value, "kernelSize")

    def test_even_error_suggests_neighbours(self):
        with pytest.raises(ValueError, match="3|5"):
            validate_median_kernel_size(4, "kernelSize")

    def test_error_message_mentions_name(self):
        with pytest.raises(ValueError, match="'kernelSize'"):
            validate_median_kernel_size(2, "kernelSize")
