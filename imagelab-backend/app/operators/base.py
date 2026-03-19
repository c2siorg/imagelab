from abc import ABC, abstractmethod

import numpy as np


class BaseOperator(ABC):
    def __init__(self, params: dict):
        self.params = params

    @abstractmethod
    def compute(self, image: np.ndarray) -> np.ndarray: ...
