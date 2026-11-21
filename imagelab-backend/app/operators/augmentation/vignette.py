import cv2
import numpy as np

from app.operators.base import BaseOperator


def _safe_float(val: object, default: float) -> float:
    try:
        return float(str(val).strip())
    except (TypeError, ValueError):
        return default


class VignetteFilter(BaseOperator):
    """Applies a radial vignette optical falloff effect to an image.

    Simulates natural camera lens shading by smoothly decreasing peripheral
    brightness toward the image edges using separable 2D Gaussian kernels.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("VignetteFilter received an invalid or empty image.")

        if not (image.ndim == 2 or (image.ndim == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(
                f"VignetteFilter expects a 2-D or 3-D image with 1, 3, or 4 channels, got shape {image.shape}."
            )

        if image.dtype != np.uint8:
            raise ValueError(f"VignetteFilter expects a uint8 image, got dtype={image.dtype}.")

        radius = max(0.1, min(2.0, _safe_float(self.params.get("radius", 0.8), 0.8)))
        intensity = max(0.0, min(1.0, _safe_float(self.params.get("intensity", 0.6), 0.6)))

        if intensity == 0.0:
            return image.copy()

        h, w = image.shape[:2]
        sigma_x = max(1.0, float(w) * radius / 2.0)
        sigma_y = max(1.0, float(h) * radius / 2.0)

        kx = cv2.getGaussianKernel(w, sigma_x).astype(np.float32)
        ky = cv2.getGaussianKernel(h, sigma_y).astype(np.float32)

        max_x = float(kx.max())
        nx = (kx / max_x) if max_x > 0 else np.ones_like(kx)
        max_y = float(ky.max())
        ny = (ky / max_y) if max_y > 0 else np.ones_like(ky)
        nx_T = nx.T

        result = np.empty_like(image)
        one_minus_int = np.float32(1.0 - intensity)
        inv_scale = np.float32(intensity)

        if image.ndim == 2:
            for y in range(h):
                row_falloff = one_minus_int + (inv_scale * float(ny[y, 0])) * nx_T
                result[y] = np.clip(image[y].astype(np.float32) * row_falloff, 0, 255).astype(np.uint8)
            return result

        if image.shape[2] == 1:
            for y in range(h):
                row_falloff = one_minus_int + (inv_scale * float(ny[y, 0])) * nx_T
                result[y, :, 0] = np.clip(image[y, :, 0].astype(np.float32) * row_falloff, 0, 255).astype(np.uint8)
            return result

        if image.shape[2] == 4:
            result[:, :, 3] = image[:, :, 3]
            for y in range(h):
                row_falloff = one_minus_int + (inv_scale * float(ny[y, 0])) * nx_T
                result[y, :, :3] = np.clip(
                    image[y, :, :3].astype(np.float32) * row_falloff[:, :, np.newaxis], 0, 255
                ).astype(np.uint8)
            return result

        # 3-channel BGR
        for y in range(h):
            row_falloff = one_minus_int + (inv_scale * float(ny[y, 0])) * nx_T
            result[y] = np.clip(image[y].astype(np.float32) * row_falloff[:, :, np.newaxis], 0, 255).astype(np.uint8)
        return result
