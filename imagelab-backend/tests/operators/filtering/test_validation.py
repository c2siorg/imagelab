import pytest

from app.operators.filtering.validation import validate_anchor_point


class TestValidateAnchorPoint:
    """validate_anchor_point — used by BoxFilter, Erosion and Dilation for point_x / point_y."""

    @pytest.mark.parametrize("value", [-1, 0, 1, 2])
    def test_valid_values_for_kernel_of_three(self, value):
        validate_anchor_point(value, 3, "point_x")

    @pytest.mark.parametrize("value", [3, 10, -2, -10])
    def test_out_of_range_values_raise(self, value):
        with pytest.raises(ValueError, match="'point_x'"):
            validate_anchor_point(value, 3, "point_x")

    def test_error_message_shows_valid_range_and_value(self):
        with pytest.raises(ValueError, match=r"between 0 and 2 .* got 10"):
            validate_anchor_point(10, 3, "point_x")

    @pytest.mark.parametrize("non_int", [1.0, "1", None])
    def test_non_integer_raises_type_error(self, non_int):
        with pytest.raises(TypeError, match="'point_y'"):
            validate_anchor_point(non_int, 3, "point_y")  # type: ignore[arg-type]
