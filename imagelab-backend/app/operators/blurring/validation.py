def validate_positive_kernel_dim(value: int, name: str) -> None:
    """Raise ValueError if value is not a positive integer."""
    if value <= 0:
        raise ValueError(
            f"'{name}' must be a positive integer, got {value}. "
            "Use a value of 1 or greater."
        )


def validate_positive_odd_kernel_size(value: int, name: str) -> None:
    """Raise ValueError if value is not a positive odd integer (required by GaussianBlur)."""
    if value <= 0:
        raise ValueError(
            f"'{name}' must be a positive odd integer, got {value}. "
            "Use a value like 1, 3, 5, 7, …"
        )
    if value % 2 == 0:
        raise ValueError(
            f"'{name}' must be a positive odd integer, got {value} (even). "
            f"Did you mean {value - 1} or {value + 1}?"
        )


def validate_median_kernel_size(value: int, name: str) -> None:
    """Raise ValueError if value is not an odd integer greater than 1 (required by medianBlur)."""
    if value <= 1:
        raise ValueError(
            f"'{name}' must be an odd integer greater than 1, got {value}. "
            "Use a value like 3, 5, 7, …"
        )
    if value % 2 == 0:
        raise ValueError(
            f"'{name}' must be an odd integer greater than 1, got {value} (even). "
            f"Did you mean {value - 1} or {value + 1}?"
        )
