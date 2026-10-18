"""
Input validators for filtering operator parameters.

Each function raises ValueError with a user-friendly message if the provided
value violates the constraint required by the underlying OpenCV call. Callers
are expected to cast raw parameter values to appropriate types before calling
these helpers.

Validators:
  validate_positive_kernel_dim      - used by BilateralFilter (filterSize), BoxFilter (width, height)
  validate_positive_number          - used for positive numeric parameters
  validate_anchor_point             - used by BoxFilter, Erosion, Dilation (point_x, point_y)
"""


def _require_int(value: object, name: str) -> None:
    """Raise TypeError if value is not a plain int.

    Python does not enforce type annotations at runtime, so float inputs like
    3.0 or 2.5 would otherwise slip through the validation checks. This guard
    must be called before any arithmetic validation.
    """
    if not isinstance(value, int):
        raise TypeError(f"'{name}' must be an integer, got {type(value).__name__}: {value!r}")


def validate_positive_kernel_dim(value: int, name: str) -> None:
    """Raise ValueError if value is not a positive integer.

    Used by BilateralFilter for filterSize and BoxFilter for width and height.
    OpenCV requires a positive integer for these kernel dimensions.

    Args:
        value: The value to validate.
        name: The parameter name (for error messages).

    Raises:
        TypeError: If value is not an int.
        ValueError: If value is not positive (> 0).
    """
    _require_int(value, name)
    if value <= 0:
        raise ValueError(f"'{name}' must be a positive integer, got {value}. Use a value of 1 or greater.")


def validate_positive_number(value: float, name: str) -> None:
    """Raise ValueError if value is not a positive number.

    Used for floating-point parameters like sigmaColor and sigmaSpace in
    BilateralFilter.

    Args:
        value: The value to validate.
        name: The parameter name (for error messages).

    Raises:
        ValueError: If value is not positive (> 0).
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"'{name}' must be a number, got {type(value).__name__}: {value!r}")
    if value <= 0:
        raise ValueError(f"'{name}' must be a positive number, got {value}. Use a value greater than 0.")


def validate_anchor_point(value: int, kernel_dim: int, name: str) -> None:
    """Raise ValueError if value is not a valid anchor position for the kernel.

    OpenCV requires the anchor to be -1 (kernel centre) or inside the kernel,
    i.e. 0 <= value < kernel_dim. Otherwise cv2.boxFilter, cv2.erode and
    cv2.dilate fail with a raw assertion error.

    Used by BoxFilter, Erosion and Dilation for point_x and point_y.
    """
    _require_int(value, name)
    if value == -1 or 0 <= value < kernel_dim:
        return
    raise ValueError(
        f"'{name}' must be -1 (centre) or between 0 and {kernel_dim - 1} "
        f"for a kernel size of {kernel_dim}, got {value}."
    )
