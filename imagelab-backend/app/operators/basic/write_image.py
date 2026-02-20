import numpy as np

from app.operators.base import BaseOperator


class WriteImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        return image
