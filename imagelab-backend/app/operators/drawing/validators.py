"""Validators for drawing operators parameters."""


class DrawingValidator:
    """Utility class for validating drawing operator parameters."""

    @staticmethod
    def validate_thickness(thickness, min_value=1):
        """
        Validate and clamp thickness parameter to a minimum value.

        Args:
            thickness: The thickness value to validate
            min_value: Minimum allowed thickness (default: 1)

        Returns:
            int: Validated thickness clamped to minimum value
        """
        return max(min_value, int(thickness))

    @staticmethod
    def validate_scale(scale, min_value=0.1):
        """
        Validate and clamp scale parameter to a minimum value.

        Args:
            scale: The scale value to validate
            min_value: Minimum allowed scale (default: 0.1)

        Returns:
            float: Validated scale clamped to minimum value
        """
        return max(min_value, float(scale))

    @staticmethod
    def validate_axis(axis, min_value=1):
        """
        Validate and clamp axis parameter (width/height/radius) to a minimum value.

        Args:
            axis: The axis value to validate
            min_value: Minimum allowed axis value (default: 1)

        Returns:
            int: Validated axis clamped to minimum value
        """
        return max(min_value, int(axis))
