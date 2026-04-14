import cv2
import numpy as np

from app.operators.base import BaseOperator

MAX_SP = 200
MAX_SR = 300
MAX_PROCESSING_DIM = 800


class MeanShiftSegmentation(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        sp = int(self.params.get("sp", 21))
        sr = int(self.params.get("sr", 51))
        max_level = int(self.params.get("maxLevel", 1))

        sp = max(1, min(sp, MAX_SP))
        sr = max(1, min(sr, MAX_SR))
        max_level = max(0, min(max_level, 4))

        if len(image.shape) == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            gray = image if len(image.shape) == 2 else image[:, :, 0]
            image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        original_h, original_w = image.shape[:2]
        scale = min(MAX_PROCESSING_DIM / original_w, MAX_PROCESSING_DIM / original_h, 1.0)
        if scale < 1.0:
            small_w = max(1, int(original_w * scale))
            small_h = max(1, int(original_h * scale))
            working = cv2.resize(image, (small_w, small_h), interpolation=cv2.INTER_AREA)
        else:
            working = image.copy()

        result_small = cv2.pyrMeanShiftFiltering(working, sp, sr, maxLevel=max_level)

        if scale < 1.0:
            return cv2.resize(result_small, (original_w, original_h), interpolation=cv2.INTER_LINEAR)
        return result_small
