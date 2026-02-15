from abc import ABC, abstractmethod

class LinearSolver(ABC):
    @abstractmethod
    def Solve(self, matrix, vector): ...
