"""
Input validators for filtering operator parameters.

Each function raises ValueError with a user-friendly message if the provided
value violates the constraint required by the underlying OpenCV call. Callers
are expected to cast raw parameter values to appropriate types before calling
these helpers.

Validators:
  validate_positive_kernel_dim      - used by BilateralFilter (filterSize)
  validate_positive_number          - used for positive numeric parameters
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

    Used by BilateralFilter for filterSize. OpenCV's bilateralFilter requires
    a positive integer for the filter diameter.

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
