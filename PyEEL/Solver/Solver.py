from abc import ABC, abstractmethod
import numpy as np

class LinearSolver(ABC):
    @abstractmethod
    def Solve(self, matrix: np.ndarray, vector: np.ndarray) -> np.ndarray: ...
    
# Common solvers
class NumpySolver(LinearSolver):
    def Solve(self, matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
        return np.linalg.solve(matrix, vector)
