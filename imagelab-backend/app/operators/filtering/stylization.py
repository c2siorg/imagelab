import cv2
import numpy as np

from app.operators.base import BaseOperator


def _safe_float(val: object, default: float) -> float:
    try:
        return float(str(val).strip())
    except (TypeError, ValueError):
        return default


class Stylization(BaseOperator):
    """Applies edge-preserving non-photorealistic stylization filtering.

    Utilizes recursive domain-transform algorithms (Gastal & Oliveira, 2011) to produce:
      - WATERCOLOR: Smooth painterly gradients with preserved sharp edge boundaries.
      - PENCIL_GRAY: High-contrast monochromatic graphite pencil sketch.
      - PENCIL_COLOR: Colored pencil sketch preserving chromatic palette and contours.
      - DETAIL_ENHANCE: Sharpens fine structural details while maintaining flat regions.

    Preserves input channel dimensionality across 2D, 1-channel, 3-channel BGR,
    and 4-channel BGRA formats.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("Stylization received an invalid or empty image.")

        if not (image.ndim == 2 or (image.ndim == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(
                f"Stylization expects a 2-D or 3-D image with 1, 3, or 4 channels, got shape {image.shape}."
            )

        if image.dtype != np.uint8:
            raise ValueError(f"Stylization expects a uint8 image, got dtype={image.dtype}.")

        mode = str(self.params.get("mode", "WATERCOLOR")).upper()
        if mode not in ("WATERCOLOR", "PENCIL_GRAY", "PENCIL_COLOR", "DETAIL_ENHANCE"):
            mode = "WATERCOLOR"

        sigma_s = max(1.0, min(200.0, _safe_float(self.params.get("sigma_s", 60.0), 60.0)))
        sigma_r = max(0.01, min(1.0, _safe_float(self.params.get("sigma_r", 0.45), 0.45)))
        shade_factor = max(0.01, min(0.1, _safe_float(self.params.get("shade_factor", 0.05), 0.05)))

        # Prepare 3-channel BGR image required by OpenCV domain transform
        if image.ndim == 2:
            proc_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.ndim == 3 and image.shape[2] == 1:
            proc_bgr = cv2.cvtColor(image[:, :, 0], cv2.COLOR_GRAY2BGR)
        elif image.ndim == 3 and image.shape[2] == 4:
            proc_bgr = np.ascontiguousarray(image[:, :, :3])
        else:
            proc_bgr = np.ascontiguousarray(image)

        # Compute stylized result
        if mode == "WATERCOLOR":
            out_bgr = cv2.stylization(proc_bgr, sigma_s=sigma_s, sigma_r=sigma_r)
            gray_sketch = None
        elif mode == "PENCIL_GRAY":
            gray_sketch, _ = cv2.pencilSketch(proc_bgr, sigma_s=sigma_s, sigma_r=sigma_r, shade_factor=shade_factor)
            out_bgr = cv2.cvtColor(gray_sketch, cv2.COLOR_GRAY2BGR)
        elif mode == "PENCIL_COLOR":
            _, out_bgr = cv2.pencilSketch(proc_bgr, sigma_s=sigma_s, sigma_r=sigma_r, shade_factor=shade_factor)
            gray_sketch = None
        else:  # DETAIL_ENHANCE
            out_bgr = cv2.detailEnhance(proc_bgr, sigma_s=sigma_s, sigma_r=sigma_r)
            gray_sketch = None

        # Format output to preserve input image channel layout
        if image.ndim == 2:
            if gray_sketch is not None:
                return gray_sketch
            return cv2.cvtColor(out_bgr, cv2.COLOR_BGR2GRAY)

        if image.ndim == 3 and image.shape[2] == 1:
            if gray_sketch is not None:
                return gray_sketch[:, :, np.newaxis]
            return cv2.cvtColor(out_bgr, cv2.COLOR_BGR2GRAY)[:, :, np.newaxis]

        if image.ndim == 3 and image.shape[2] == 4:
            return np.dstack((out_bgr, image[:, :, 3]))

        return out_bgr
