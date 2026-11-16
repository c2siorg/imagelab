import cv2
import numpy as np

from app.operators.base import BaseOperator


class InRangeThreshold(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        h_min = int(max(0, min(179, int(float(self.params.get("h_min", 0))))))
        h_max = int(max(0, min(179, int(float(self.params.get("h_max", 179))))))
        s_min = int(max(0, min(255, int(float(self.params.get("s_min", 0))))))
        s_max = int(max(0, min(255, int(float(self.params.get("s_max", 255))))))
        v_min = int(max(0, min(255, int(float(self.params.get("v_min", 0))))))
        v_max = int(max(0, min(255, int(float(self.params.get("v_max", 255))))))

        raw_mask_only = self.params.get("output_mask_only", False)
        if isinstance(raw_mask_only, str):
            output_mask_only = raw_mask_only.strip().lower() in ("true", "1", "yes")
        else:
            output_mask_only = bool(raw_mask_only)

        alpha_channel = None
        if image.ndim == 2:
            bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.ndim == 3 and image.shape[2] == 1:
            bgr = cv2.cvtColor(image[:, :, 0], cv2.COLOR_GRAY2BGR)
        elif image.ndim == 3 and image.shape[2] == 4:
            bgr = image[:, :, :3]
            alpha_channel = image[:, :, 3]
        else:
            bgr = image

        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        lower_bound = np.array([h_min, s_min, v_min], dtype=np.uint8)
        upper_bound = np.array([h_max, s_max, v_max], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_bound, upper_bound)

        if output_mask_only:
            return mask

        masked_bgr = cv2.bitwise_and(bgr, bgr, mask=mask)
        if alpha_channel is not None:
            return np.dstack([masked_bgr, alpha_channel])

        return masked_bgr
