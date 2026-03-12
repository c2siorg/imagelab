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

    @pytest.mark.parametrize("non_int", [1.0, 3.5, "3", None])
    def test_non_integer_raises_type_error(self, non_int):
        with pytest.raises(TypeError, match="'widthSize'"):
            validate_positive_kernel_dim(non_int, "widthSize")  # type: ignore[arg-type]


class TestValidatePositiveOddKernelSize:
    """validate_positive_odd_kernel_size — used by GaussianBlur."""

    @pytest.mark.parametrize("value", [1, 3, 5, 7, 9, 101])
    def test_valid_positive_odd_values(self, value):
        validate_positive_odd_kernel_size(value, "widthSize")

    @pytest.mark.parametrize("value", [2, 4, 6, 100])
    def test_even_values_corrected_to_odd(self, value):
        result = validate_positive_odd_kernel_size(value, "widthSize")
        assert result == value + 1
        assert result % 2 != 0

    @pytest.mark.parametrize("value", [0, -1, -3])
    def test_invalid_non_positive_values(self, value):
        with pytest.raises(ValueError, match="'widthSize'"):
            validate_positive_odd_kernel_size(value, "widthSize")



    def test_even_value_2_corrected_to_3(self):
        assert validate_positive_odd_kernel_size(2, "heightSize") == 3

    @pytest.mark.parametrize("non_int", [1.0, 3.5, "3", None])
    def test_non_integer_raises_type_error(self, non_int):
        with pytest.raises(TypeError, match="'widthSize'"):
            validate_positive_odd_kernel_size(non_int, "widthSize")  # type: ignore[arg-type]


class TestValidateMedianKernelSize:
    """validate_median_kernel_size — used by MedianBlur."""

    @pytest.mark.parametrize("value", [1, 3, 5, 7, 9, 101])
    def test_valid_odd_values(self, value):
        validate_median_kernel_size(value, "kernelSize")

    @pytest.mark.parametrize("value", [2, 4, 6, 8, 100])
    def test_even_values_corrected_to_odd(self, value):
        result = validate_median_kernel_size(value, "kernelSize")
        assert result == value + 1
        assert result % 2 != 0

    @pytest.mark.parametrize("value", [0, -1, -5])
    def test_invalid_values_below_minimum(self, value):
        """Values < 1 are invalid; the error message must reference the minimum."""
        with pytest.raises(ValueError, match=">= 1"):
            validate_median_kernel_size(value, "kernelSize")

    @pytest.mark.parametrize("non_int", [3.0, 5.5, "3", None])
    def test_non_integer_raises_type_error(self, non_int):
        with pytest.raises(TypeError, match="'kernelSize'"):
            validate_median_kernel_size(non_int, "kernelSize")  # type: ignore[arg-type]
