from .Node import Node
from .NodeManager import NodeManager
from .SimulationContext import SimulationContext, SimulationMode
from .Components.Component import Component
from .Solver.Solver import LinearSolver

import numpy as np

class Circuit:
    _NodeManager: NodeManager
    _Components: list[Component]
    _Solver: LinearSolver
    _Finalized: bool
    
    __T: float
    __x_prev: np.ndarray | None
    
    def __init__(self, solver: LinearSolver):
        self._NodeManager = NodeManager()
        self._Components = []
        self._Solver = solver
        self._Finalized = False
        
        self.__T = 0.0
        self.__x_prev = None
        
    @property
    def NodeManager(self) -> NodeManager: return self._NodeManager
    @property
    def Time(self) -> float: return self.__T
    
    def ResetTime(self) -> None:
        self.__T = 0.0
    
    def AddComponent(self, component: Component) -> None:
        if self._Finalized:
            raise RuntimeError("Cannot add component to a finalized circuit.")
        
        self._Components.append(component)
        
    def Finalize(self) -> None:
        if self._Finalized:
            raise RuntimeError("Circuit is already finalized.")
        
        # Freeze the NodeManager to prevent further modifications
        self._NodeManager.Freeze()
        
        # Register unknowns for all components
        for component in self._Components:
            component.RegisterUnknowns(self._NodeManager)
        
        self._Finalized = True
        
        
    def _BuildSystem(self, context) -> tuple:
        # Build the system of equations
        A = np.zeros((self._NodeManager.TotalUnknownCount, self._NodeManager.TotalUnknownCount))
        b = np.zeros(self._NodeManager.TotalUnknownCount)
        
        for component in self._Components:
            component.Stamp(A, b, context)
        
        return A, b
    
    def Simulate(self, dt) -> np.ndarray:
        if not self._Finalized:
            raise RuntimeError("Circuit must be finalized before simulation.")
        
        context = SimulationContext(
            Mode=SimulationMode.TRANSIENT,
            Time=self.__T,
            dt=dt,
            x_prev=self.__x_prev  # Previous solution can be stored and passed here for time-varying simulations
        )
        
        A, b = self._BuildSystem(context)  # Context can be extended for time-varying simulations
        solution = self._Solver.Solve(A, b)
        
        for component in self._Components:
            component.UpdateState(solution, context)
        
        self.__x_prev = solution
        self.__T += dt
        
        return solution
