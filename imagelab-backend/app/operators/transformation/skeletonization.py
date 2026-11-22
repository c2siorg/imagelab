import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


def _safe_int(val: object, default: int) -> int:
    try:
        return int(float(str(val).strip()))
    except (TypeError, ValueError):
        return default


def _safe_bool(val: object, default: bool = False) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        v = val.strip().lower()
        if v in ("true", "1", "yes", "on"):
            return True
        if v in ("false", "0", "no", "off"):
            return False
    return default


class Skeletonization(BaseOperator):
    """Computes the morphological skeleton (topological medial axis) of shapes.

    Iteratively thins foreground shapes using morphological erosion and opening
    subtractions until convergence (or reaching max_iterations):
        S_k(A) = (A ⊖ kB) - ((A ⊖ kB) ∘ B)
        Skeleton(A) = ⋃_k S_k(A)

    Preserves shape topology, connectivity, and endpoint structure for OCR,
    stroke extraction, fingerprint analysis, and vascular network analysis.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("Skeletonization received an invalid or empty image.")

        if not (image.ndim == 2 or (image.ndim == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(
                f"Skeletonization expects a 2-D or 3-D image with 1, 3, or 4 channels, got shape {image.shape}."
            )

        if image.dtype != np.uint8:
            raise ValueError(f"Skeletonization expects a uint8 image, got dtype={image.dtype}.")

        element_str = str(self.params.get("element", "CROSS")).upper()
        if element_str not in ("CROSS", "RECTANGLE", "ELLIPSE"):
            element_str = "CROSS"

        elem_map = {
            "CROSS": cv2.MORPH_CROSS,
            "RECTANGLE": cv2.MORPH_RECT,
            "ELLIPSE": cv2.MORPH_ELLIPSE,
        }
        struct_elem = elem_map[element_str]

        kernel_size = _safe_int(self.params.get("kernel_size", 3), 3)
        kernel_size = max(3, min(15, kernel_size))
        if kernel_size % 2 == 0:
            kernel_size += 1

        max_iterations = max(0, min(500, _safe_int(self.params.get("max_iterations", 0), 0)))
        threshold_val = max(0, min(255, _safe_int(self.params.get("threshold", 127), 127)))
        invert = _safe_bool(self.params.get("invert", False), False)

        output_mode = str(self.params.get("output_mode", "BINARY_MASK")).upper()
        if output_mode not in ("BINARY_MASK", "OVERLAY"):
            output_mode = "BINARY_MASK"

        try:
            bgr_color = hex_to_bgr(str(self.params.get("skeleton_color", "#00ffff")))
        except (TypeError, ValueError):
            bgr_color = (255, 255, 0)

        # Convert to single-channel grayscale
        if image.ndim == 2:
            gray = image
        elif image.ndim == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
        elif image.ndim == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Binarize
        _, binary = cv2.threshold(gray, threshold_val, 255, cv2.THRESH_BINARY)
        if invert:
            binary = cv2.bitwise_not(binary)

        # Early exit for empty binary mask
        if cv2.countNonZero(binary) == 0:
            if output_mode == "OVERLAY":
                return image.copy()
            if image.ndim == 2:
                return np.zeros_like(binary)
            if image.ndim == 3 and image.shape[2] == 1:
                return np.zeros((image.shape[0], image.shape[1], 1), dtype=np.uint8)
            if image.ndim == 3 and image.shape[2] == 4:
                return np.zeros((image.shape[0], image.shape[1], 4), dtype=np.uint8)
            return np.zeros((image.shape[0], image.shape[1], 3), dtype=np.uint8)

        # Iterative morphological skeletonization with hard safety ceiling against runaway DoS
        max_loop_limit = max_iterations if max_iterations > 0 else 1000
        kernel = cv2.getStructuringElement(struct_elem, (kernel_size, kernel_size))
        skel = np.zeros_like(binary)
        current = binary.copy()
        iters = 0

        while True:
            eroded = cv2.erode(current, kernel)
            opened = cv2.dilate(eroded, kernel)
            temp = cv2.subtract(current, opened)
            skel = cv2.bitwise_or(skel, temp)
            current = eroded
            iters += 1
            if cv2.countNonZero(current) == 0 or iters >= max_loop_limit:
                break

        # Standard Rec. 601 perceptual luminance for monochromatic output
        gray_col = int(round(0.114 * bgr_color[0] + 0.587 * bgr_color[1] + 0.299 * bgr_color[2]))

        if output_mode == "OVERLAY":
            result = image.copy()
            if image.ndim == 2:
                result[skel > 0] = gray_col
            elif image.ndim == 3 and image.shape[2] == 1:
                result[skel > 0, 0] = gray_col
            elif image.ndim == 3 and image.shape[2] == 4:
                result[skel > 0, :3] = bgr_color
                result[skel > 0, 3] = 255
            else:
                result[skel > 0] = bgr_color
            return result

        # BINARY_MASK output mode: preserve input image channel layout
        if image.ndim == 2:
            return skel
        if image.ndim == 3 and image.shape[2] == 1:
            return skel[:, :, np.newaxis]
        if image.ndim == 3 and image.shape[2] == 4:
            bgr = cv2.cvtColor(skel, cv2.COLOR_GRAY2BGR)
            alpha_out = image[:, :, 3].copy()
            alpha_out[skel > 0] = 255
            return np.dstack((bgr, alpha_out))
        return cv2.cvtColor(skel, cv2.COLOR_GRAY2BGR)
