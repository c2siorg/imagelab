import base64

import cv2
import numpy as np


def decode_base64_image(b64: str) -> np.ndarray:
    data = base64.b64decode(b64)
    arr = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("Could not decode image data")
    return image


def encode_image_base64(image: np.ndarray, fmt: str = "png") -> str:
    success, buf = cv2.imencode(f".{fmt}", image)
    if not success:
        raise ValueError(f"Could not encode image as {fmt}")
    return base64.b64encode(buf).decode("utf-8")


def compute_image_stats(image: np.ndarray) -> dict:
    """Compute pixel statistics and per-channel histograms for an image.

    Returns a plain dict (not a Pydantic model) to avoid coupling utils to
    the models layer.  The executor converts this dict into an ``ImageStats``
    model.

    Float images are normalised to [0, 255] before histogram computation so
    that ``cv2.calcHist`` produces meaningful bucket counts regardless of the
    original value range.  Alpha channels are excluded from histograms.
    """
    h, w = image.shape[:2]
    channels = 1 if image.ndim == 2 else image.shape[2]
    dtype = str(image.dtype)

    flat = image.flatten().astype(np.float64)
    mn = float(flat.min())
    mx = float(flat.max())
    mean_val = round(float(flat.mean()), 3)

    # Normalise to uint8 for histogram computation.
    # float images may have arbitrary ranges; integer images > uint8 need scaling too.
    if mx > mn:
        img_u8 = ((image.astype(np.float64) - mn) / (mx - mn) * 255).clip(0, 255).astype(np.uint8)
    else:
        # Uniform image — preserve the actual pixel value in [0, 255] so that the
        # histogram bucket reflects the true intensity (e.g. all-128 → bucket 128).
        val = int(np.clip(mn, 0, 255))
        img_u8 = np.full(image.shape, val, dtype=np.uint8)

    histograms: list[list[int]] = []
    n_hist_channels = 1 if img_u8.ndim == 2 else min(img_u8.shape[2], 3)  # max 3 (no alpha)
    for c in range(n_hist_channels):
        channel = img_u8 if img_u8.ndim == 2 else img_u8[:, :, c]
        hist = cv2.calcHist([channel], [0], None, [256], [0, 256])
        histograms.append(hist.flatten().astype(int).tolist())

    return {
        "width": w,
        "height": h,
        "channels": channels,
        "dtype": dtype,
        "min_val": mn,
        "max_val": mx,
        "mean_val": mean_val,
        "histograms": histograms,
    }
