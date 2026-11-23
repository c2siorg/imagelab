import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


def _safe_int(val: object, default: int) -> int:
    try:
        return int(float(str(val).strip()))
    except (TypeError, ValueError):
        return default


class Cutout(BaseOperator):
    """Applies Cutout / Random Erasing regularizing data augmentation.

    Masks out random square or rectangular patches of the image with constant
    color, Gaussian/uniform noise, or channel means. Regularizes deep vision
    models against feature co-dependence and localized occlusion.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("Cutout received an invalid or empty image.")

        if not (image.ndim == 2 or (image.ndim == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(f"Cutout expects a 2-D or 3-D image with 1, 3, or 4 channels, got shape {image.shape}.")

        if image.dtype != np.uint8:
            raise ValueError(f"Cutout expects a uint8 image, got dtype={image.dtype}.")

        num_holes = max(1, min(20, _safe_int(self.params.get("num_holes", 1), 1)))
        hole_size = max(4, min(512, _safe_int(self.params.get("hole_size", 32), 32)))
        fill_mode = str(self.params.get("fill_mode", "CONSTANT")).upper()
        if fill_mode not in ("CONSTANT", "RANDOM_NOISE", "MEAN"):
            fill_mode = "CONSTANT"

        try:
            bgr_color = hex_to_bgr(str(self.params.get("fill_color", "#000000")))
        except (TypeError, ValueError):
            bgr_color = (0, 0, 0)

        seed = _safe_int(self.params.get("seed", 0), 0)
        rng = np.random.default_rng(seed) if seed > 0 else np.random.default_rng()

        result = image.copy()
        h, w = image.shape[:2]

        # Precompute mean channel values if fill_mode is MEAN
        if fill_mode == "MEAN":
            if image.ndim == 2:
                mean_val = int(round(float(np.mean(image))))
            elif image.ndim == 3 and image.shape[2] == 1:
                mean_val = int(round(float(np.mean(image[:, :, 0]))))
            elif image.ndim == 3 and image.shape[2] == 4:
                mean_val = [int(round(float(np.mean(image[:, :, c])))) for c in range(3)]
            else:
                mean_val = [int(round(float(np.mean(image[:, :, c])))) for c in range(3)]

        half_size = hole_size // 2
        rem_size = hole_size - half_size
        gray_col = int(round(0.114 * bgr_color[0] + 0.587 * bgr_color[1] + 0.299 * bgr_color[2]))

        for _ in range(num_holes):
            cx = int(rng.integers(0, w))
            cy = int(rng.integers(0, h))

            x1 = max(0, cx - half_size)
            y1 = max(0, cy - half_size)
            x2 = min(w, cx + rem_size)
            y2 = min(h, cy + rem_size)

            if x2 <= x1 or y2 <= y1:
                continue

            patch_h = y2 - y1
            patch_w = x2 - x1

            if fill_mode == "CONSTANT":
                if image.ndim == 2:
                    result[y1:y2, x1:x2] = gray_col
                elif image.ndim == 3 and image.shape[2] == 1:
                    result[y1:y2, x1:x2, 0] = gray_col
                elif image.ndim == 3 and image.shape[2] == 4:
                    result[y1:y2, x1:x2, :3] = bgr_color
                else:
                    result[y1:y2, x1:x2] = bgr_color

            elif fill_mode == "RANDOM_NOISE":
                if image.ndim == 2:
                    noise = rng.integers(0, 256, size=(patch_h, patch_w), dtype=np.uint8)
                    result[y1:y2, x1:x2] = noise
                elif image.ndim == 3 and image.shape[2] == 1:
                    noise = rng.integers(0, 256, size=(patch_h, patch_w, 1), dtype=np.uint8)
                    result[y1:y2, x1:x2] = noise
                elif image.ndim == 3 and image.shape[2] == 4:
                    noise = rng.integers(0, 256, size=(patch_h, patch_w, 3), dtype=np.uint8)
                    result[y1:y2, x1:x2, :3] = noise
                else:
                    noise = rng.integers(0, 256, size=(patch_h, patch_w, 3), dtype=np.uint8)
                    result[y1:y2, x1:x2] = noise

            elif fill_mode == "MEAN":
                if image.ndim == 2:
                    result[y1:y2, x1:x2] = mean_val
                elif image.ndim == 3 and image.shape[2] == 1:
                    result[y1:y2, x1:x2, 0] = mean_val
                elif image.ndim == 3 and image.shape[2] == 4:
                    result[y1:y2, x1:x2, :3] = mean_val
                else:
                    result[y1:y2, x1:x2] = mean_val

        return result
