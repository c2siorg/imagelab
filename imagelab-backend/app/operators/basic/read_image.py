import numpy as np

from app.operators.base import BaseOperator


class ReadImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        return image
