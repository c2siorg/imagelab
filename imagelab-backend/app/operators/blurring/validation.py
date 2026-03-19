"""
Input validators for blurring operator parameters.

Each function raises ValueError with a user-friendly message if the provided
value violates the constraint required by the underlying OpenCV call. Callers
are expected to cast raw parameter values to int before calling these helpers.

Validators:
  validate_positive_kernel_dim      - used by Blur (widthSize, heightSize)
  validate_positive_odd_kernel_size - used by GaussianBlur (widthSize, heightSize)
  validate_median_kernel_size       - used by MedianBlur (kernelSize)
"""


def _require_int(value: object, name: str) -> None:
    """Raise TypeError if value is not a plain int.

    Python does not enforce type annotations at runtime, so float inputs like
    3.0 or 2.5 would otherwise slip through the odd/positive checks. This
    guard must be called before any arithmetic validation.
    """
    if not isinstance(value, int):
        raise TypeError(f"'{name}' must be an integer, got {type(value).__name__}: {value!r}")


def _validate_odd_kernel(value: int, name: str, min_value: int, examples: str) -> None:
    """Shared logic for odd-kernel validators.

    Raises ValueError when value is below min_value or even. The lower-neighbour
    suggestion for even values is only included when it is itself >= min_value,
    preventing suggestions of invalid values (e.g. when value=2 and min_value=3,
    only 3 is suggested, never 1).
    """
    if value < min_value:
        raise ValueError(
            f"'{name}' must be a positive odd integer >= {min_value}, got {value}. Use a value like {examples}."
        )
    if value % 2 == 0:
        lower = value - 1
        upper = value + 1
        suggestion = f"{lower} or {upper}" if lower >= min_value else str(upper)
        raise ValueError(
            f"'{name}' must be a positive odd integer >= {min_value}, got {value} (even). Did you mean {suggestion}?"
        )


def validate_positive_kernel_dim(value: int, name: str) -> None:
    """Raise ValueError if value is not a positive integer.

    Used by Blur for widthSize and heightSize.
    """
    _require_int(value, name)
    if value <= 0:
        raise ValueError(f"'{name}' must be a positive integer, got {value}. Use a value of 1 or greater.")


def validate_positive_odd_kernel_size(value: int, name: str) -> None:
    """Raise ValueError if value is not a positive odd integer.

    Used by GaussianBlur for widthSize and heightSize. OpenCV requires the
    kernel size to be a positive odd integer.
    """
    _require_int(value, name)
    _validate_odd_kernel(value, name, min_value=1, examples="1, 3, 5, 7")


def validate_median_kernel_size(value: int, name: str) -> None:
    """Raise ValueError if value is not a valid MedianBlur kernel size.

    OpenCV technically accepts ksize=1 (identity operation), but this validator
    rejects it to prevent accidentally passing a no-op blur. Valid values are
    odd integers >= 3 (e.g. 3, 5, 7).

    Used by MedianBlur for kernelSize.
    """
    _require_int(value, name)
    _validate_odd_kernel(value, name, min_value=3, examples="3, 5, 7")
