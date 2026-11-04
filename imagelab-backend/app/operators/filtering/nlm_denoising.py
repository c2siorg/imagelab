import cv2
import numpy as np

from app.operators.base import BaseOperator


def _safe_float(val: object, default: float, min_val: float | None = None, max_val: float | None = None) -> float:
    try:
        res = float(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        res = default
    if min_val is not None:
        res = max(min_val, res)
    if max_val is not None:
        res = min(max_val, res)
    return res


def _safe_int(val: object, default: int, min_val: int | None = None, max_val: int | None = None) -> int:
    try:
        res = int(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        res = default
    if min_val is not None:
        res = max(min_val, res)
    if max_val is not None:
        res = min(max_val, res)
    return res


class NlmDenoising(BaseOperator):
    """Remove noise using Fast Non-Local Means (NLM) Denoising.

    Non-Local Means replaces each pixel with a weighted average of surrounding
    pixels whose local neighborhood patches resemble the target patch. Unlike
    Gaussian or Bilateral filters, NLM effectively removes sensor and grain noise
    while preserving delicate textures, repetitive patterns, and crisp object edges.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("NlmDenoising received an invalid or empty image.")

        if not (image.ndim == 2 or (image.ndim == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(
                f"NlmDenoising expects a 2-D or 3-D image with 1, 3, or 4 channels, got shape {image.shape}."
            )

        if image.dtype != np.uint8:
            raise ValueError(f"NlmDenoising expects a uint8 image, got dtype={image.dtype}.")

        h = _safe_float(self.params.get("h", 10.0), default=10.0, min_val=0.5, max_val=100.0)
        h_color = _safe_float(self.params.get("hColor", 10.0), default=10.0, min_val=0.5, max_val=100.0)

        template_size = _safe_int(self.params.get("templateWindowSize", 7), default=7, min_val=3, max_val=21)
        if template_size % 2 == 0:
            template_size += 1

        search_size = _safe_int(self.params.get("searchWindowSize", 21), default=21, min_val=5, max_val=45)
        if search_size % 2 == 0:
            search_size += 1

        if search_size <= template_size:
            search_size = template_size + 2

        # 2D Grayscale
        if image.ndim == 2:
            return cv2.fastNlMeansDenoising(
                image,
                None,
                h=h,
                templateWindowSize=template_size,
                searchWindowSize=search_size,
            )

        # 3D Single-Channel
        if image.shape[2] == 1:
            denoised = cv2.fastNlMeansDenoising(
                image[:, :, 0],
                None,
                h=h,
                templateWindowSize=template_size,
                searchWindowSize=search_size,
            )
            return denoised[:, :, np.newaxis]

        # 4D BGRA (denoise BGR channels and re-attach alpha)
        if image.shape[2] == 4:
            bgr = image[:, :, :3]
            alpha = image[:, :, 3]
            denoised_bgr = cv2.fastNlMeansDenoisingColored(
                bgr,
                None,
                h=h,
                hColor=h_color,
                templateWindowSize=template_size,
                searchWindowSize=search_size,
            )
            return np.dstack([denoised_bgr, alpha])

        # 3D BGR
        return cv2.fastNlMeansDenoisingColored(
            image,
            None,
            h=h,
            hColor=h_color,
            templateWindowSize=template_size,
            searchWindowSize=search_size,
        )
