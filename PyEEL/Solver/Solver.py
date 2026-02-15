from abc import ABC, abstractmethod
import numpy as np

class LinearSolver(ABC):
    @abstractmethod
    def Solve(self, matrix: np.ndarray, vector: np.ndarray) -> np.ndarray: ...
