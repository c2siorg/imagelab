import re

import numpy as np

HEX_COLOR_RE = re.compile(r"^[0-9a-fA-F]{6}$")


def hex_to_bgr(hex_color: str) -> tuple[int, int, int]:
    """
    Convert a 6-digit CSS hex color string to a BGR tuple for OpenCV.

    Args:
        hex_color: A 6-digit hex color string, with or without a leading '#'.

    Returns:
        A (blue, green, red) tuple of integers.

    Raises:
        TypeError: If hex_color is not a string.
        ValueError: If hex_color is not a valid 6-digit hex color string.
    """
    if not isinstance(hex_color, str):
        raise TypeError(f"hex_to_bgr expects a str, got {type(hex_color).__name__!r}")

    original = hex_color
    normalized = hex_color.removeprefix("#")

    if not HEX_COLOR_RE.fullmatch(normalized):
        raise ValueError(f"Invalid hex color: {original!r}. Expected format '#rrggbb' or 'rrggbb'.")

    r = int(normalized[0:2], 16)
    g = int(normalized[2:4], 16)
    b = int(normalized[4:6], 16)
    return (b, g, r)


def hex_to_draw_color(hex_color: str, image: np.ndarray) -> tuple[int, ...]:
    """
    Convert a 6-digit CSS hex color string to an OpenCV draw color for an image.

    Args:
        hex_color: A 6-digit hex color string, with or without a leading '#'.
        image: The image that will be drawn on.

    Returns:
        A (blue, green, red) tuple, or (blue, green, red, 255) when the image
        has an alpha channel so drawn pixels are opaque instead of transparent.
    """
    bgr = hex_to_bgr(hex_color)
    if image.ndim == 3 and image.shape[2] == 4:
        return (*bgr, 255)
    return bgr
