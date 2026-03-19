import cv2
import numpy as np

from app.operators.base import BaseOperator


class ApplyBorders(BaseOperator):
    _BORDER_TYPE_MAP: dict[str, int] = {
        "CONSTANT": cv2.BORDER_CONSTANT,
        "REFLECT": cv2.BORDER_REFLECT_101,
        "REPLICATE": cv2.BORDER_REPLICATE,
        "WRAP": cv2.BORDER_WRAP,
    }

    def compute(self, image: np.ndarray) -> np.ndarray:
        border_all = self.params.get("border_all_sides")
        if border_all is not None:
            try:
                top = bottom = left = right = max(0, int(border_all))
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid border value '{border_all}': {e}") from e
        else:
            try:
                top = max(0, int(self.params.get("borderTop", 0)))
                bottom = max(0, int(self.params.get("borderBottom", 0)))
                left = max(0, int(self.params.get("borderLeft", 0)))
                right = max(0, int(self.params.get("borderRight", 0)))
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid border side value: {e}") from e

        border_type_str = str(self.params.get("border_type", "CONSTANT")).upper()
        if border_type_str not in self._BORDER_TYPE_MAP:
            raise ValueError(
                f"Unknown border type '{border_type_str}'. Valid options: {list(self._BORDER_TYPE_MAP.keys())}"
            )
        border_type = self._BORDER_TYPE_MAP[border_type_str]

        kwargs = {"value": [0, 0, 0]} if border_type == cv2.BORDER_CONSTANT else {}
        return cv2.copyMakeBorder(image, top, bottom, left, right, border_type, **kwargs)
