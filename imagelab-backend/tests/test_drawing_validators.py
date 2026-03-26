"""Tests for drawing operators parameter validators."""

from app.operators.drawing.validators import DrawingValidator


class TestDrawingValidator:
    """Test suite for DrawingValidator class."""

    def test_validate_thickness_clamps_to_minimum(self):
        """Test that thickness is clamped to minimum value of 1."""
        assert DrawingValidator.validate_thickness(0) == 1
        assert DrawingValidator.validate_thickness(-5) == 1
        assert DrawingValidator.validate_thickness(-1) == 1

    def test_validate_thickness_keeps_valid_values(self):
        """Test that valid thickness values are preserved."""
        assert DrawingValidator.validate_thickness(1) == 1
        assert DrawingValidator.validate_thickness(2) == 2
        assert DrawingValidator.validate_thickness(10) == 10
        assert DrawingValidator.validate_thickness(100) == 100

    def test_validate_thickness_converts_to_int(self):
        """Test that thickness is converted to integer."""
        assert DrawingValidator.validate_thickness(2.5) == 2
        assert DrawingValidator.validate_thickness(1.1) == 1
        assert isinstance(DrawingValidator.validate_thickness(2.5), int)

    def test_validate_scale_clamps_to_minimum(self):
        """Test that scale is clamped to minimum value of 0.1."""
        assert DrawingValidator.validate_scale(0) == 0.1
        assert DrawingValidator.validate_scale(-5) == 0.1
        assert DrawingValidator.validate_scale(-1) == 0.1
        assert DrawingValidator.validate_scale(0.05) == 0.1

    def test_validate_scale_keeps_valid_values(self):
        """Test that valid scale values are preserved."""
        assert DrawingValidator.validate_scale(0.1) == 0.1
        assert DrawingValidator.validate_scale(1) == 1.0
        assert DrawingValidator.validate_scale(2.5) == 2.5
        assert DrawingValidator.validate_scale(10) == 10.0

    def test_validate_scale_converts_to_float(self):
        """Test that scale is converted to float."""
        assert DrawingValidator.validate_scale(1) == 1.0
        assert isinstance(DrawingValidator.validate_scale(1), float)
        assert isinstance(DrawingValidator.validate_scale(1.5), float)

    def test_validate_axis_clamps_to_minimum(self):
        """Test that axis is clamped to minimum value of 1."""
        assert DrawingValidator.validate_axis(0) == 1
        assert DrawingValidator.validate_axis(-5) == 1
        assert DrawingValidator.validate_axis(-1) == 1

    def test_validate_axis_keeps_valid_values(self):
        """Test that valid axis values are preserved."""
        assert DrawingValidator.validate_axis(1) == 1
        assert DrawingValidator.validate_axis(5) == 5
        assert DrawingValidator.validate_axis(100) == 100
        assert DrawingValidator.validate_axis(1000) == 1000

    def test_validate_axis_converts_to_int(self):
        """Test that axis is converted to integer."""
        assert DrawingValidator.validate_axis(5.7) == 5
        assert DrawingValidator.validate_axis(1.2) == 1
        assert isinstance(DrawingValidator.validate_axis(5.7), int)

    def test_validate_thickness_custom_min_value(self):
        """Test validate_thickness with custom minimum value."""
        assert DrawingValidator.validate_thickness(0, min_value=2) == 2
        assert DrawingValidator.validate_thickness(1, min_value=2) == 2
        assert DrawingValidator.validate_thickness(3, min_value=2) == 3

    def test_validate_scale_custom_min_value(self):
        """Test validate_scale with custom minimum value."""
        assert DrawingValidator.validate_scale(0, min_value=0.5) == 0.5
        assert DrawingValidator.validate_scale(0.3, min_value=0.5) == 0.5
        assert DrawingValidator.validate_scale(1, min_value=0.5) == 1.0

    def test_validate_axis_custom_min_value(self):
        """Test validate_axis with custom minimum value."""
        assert DrawingValidator.validate_axis(0, min_value=5) == 5
        assert DrawingValidator.validate_axis(3, min_value=5) == 5
        assert DrawingValidator.validate_axis(10, min_value=5) == 10
