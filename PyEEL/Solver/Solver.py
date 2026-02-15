from abc import ABC, abstractmethod
import numpy as np


class LinearSolver(ABC):
    """
    Abstract interface for solving the linear system ``A x = b``.

    Subclass this to plug in different backends (dense, sparse, iterative, etc.).
    """

    @abstractmethod
    def Solve(self, matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
        """Solve ``matrix @ x = vector`` and return **x**."""
        ...


class NumpySolver(LinearSolver):
    """Direct dense solver using :func:`numpy.linalg.solve`."""

    def Solve(self, matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
        return np.linalg.solve(matrix, vector)
