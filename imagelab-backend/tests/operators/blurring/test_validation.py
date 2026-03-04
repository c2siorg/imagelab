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
    def test_invalid_even_values(self, value):
        with pytest.raises(ValueError, match="even"):
            validate_positive_odd_kernel_size(value, "widthSize")

    @pytest.mark.parametrize("value", [0, -1, -3])
    def test_invalid_non_positive_values(self, value):
        with pytest.raises(ValueError, match="'widthSize'"):
            validate_positive_odd_kernel_size(value, "widthSize")

    @pytest.mark.parametrize(
        "even, expected_lower, expected_upper",
        [
            (2, 1, 3),
            (4, 3, 5),
            (100, 99, 101),
        ],
    )
    def test_even_error_suggests_neighbours(self, even, expected_lower, expected_upper):
        """Both neighbours are valid for GaussianBlur (min_value=1), so both must appear."""
        with pytest.raises(ValueError, match=f"{expected_lower}|{expected_upper}"):
            validate_positive_odd_kernel_size(even, "widthSize")

    def test_error_message_mentions_name(self):
        with pytest.raises(ValueError, match="'heightSize'"):
            validate_positive_odd_kernel_size(2, "heightSize")

    @pytest.mark.parametrize("non_int", [1.0, 3.5, "3", None])
    def test_non_integer_raises_type_error(self, non_int):
        with pytest.raises(TypeError, match="'widthSize'"):
            validate_positive_odd_kernel_size(non_int, "widthSize")  # type: ignore[arg-type]


class TestValidateMedianKernelSize:
    """validate_median_kernel_size — used by MedianBlur."""

    @pytest.mark.parametrize("value", [3, 5, 7, 9, 101])
    def test_valid_odd_values_greater_than_one(self, value):
        validate_median_kernel_size(value, "kernelSize")

    @pytest.mark.parametrize("value", [4, 6, 8, 100])
    def test_invalid_even_values(self, value):
        # 2 is intentionally excluded: with min_value=3, _validate_odd_kernel
        # catches 2 via the lower-bound check before the even check.
        with pytest.raises(ValueError, match="even"):
            validate_median_kernel_size(value, "kernelSize")

    @pytest.mark.parametrize("value", [2, 1, 0, -1, -5])
    def test_invalid_values_below_minimum(self, value):
        """Values < 3 are invalid; the error message must reference the minimum."""
        with pytest.raises(ValueError, match=">= 3"):
            validate_median_kernel_size(value, "kernelSize")

    @pytest.mark.parametrize(
        "even, expected_lower, expected_upper",
        [
            (4, 3, 5),
            (8, 7, 9),
            (100, 99, 101),
        ],
    )
    def test_even_error_suggests_valid_neighbours(self, even, expected_lower, expected_upper):
        """Both neighbours are >= 3, so both should appear in the suggestion."""
        with pytest.raises(ValueError, match=f"{expected_lower}|{expected_upper}"):
            validate_median_kernel_size(even, "kernelSize")

    def test_even_value_2_suggests_only_valid_neighbour(self):
        """value=2 must not suggest 1, which is itself invalid for MedianBlur."""
        with pytest.raises(ValueError) as exc_info:
            validate_median_kernel_size(2, "kernelSize")
        msg = str(exc_info.value)
        assert "3" in msg, "should suggest 3 as the smallest valid value"
        assert "1" not in msg, "must not suggest 1 (rejected by the same validator)"

    def test_error_message_mentions_name(self):
        with pytest.raises(ValueError, match="'kernelSize'"):
            validate_median_kernel_size(2, "kernelSize")

    @pytest.mark.parametrize("non_int", [3.0, 5.5, "3", None])
    def test_non_integer_raises_type_error(self, non_int):
        with pytest.raises(TypeError, match="'kernelSize'"):
            validate_median_kernel_size(non_int, "kernelSize")  # type: ignore[arg-type]
