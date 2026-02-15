from .Node import Node
from .NodeManager import NodeManager
from .SimulationContext import SimulationContext

from .Component import Component

import numpy as np

class Resister(Component):
    _Resistance: float
    
    # Current flows from the first node to the second node, etc.
    # i.e nodes[0] -> nodes[1]
    def __init__(self, name: str, nodes: tuple[Node, Node], resistance: float):
        super().__init__(name, nodes)
        self._Resistance = resistance
    
    @property
    def Resistance(self) -> float: return self._Resistance
    
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None: pass
    
    def Stamp(self, A: np.ndarray, b: np.ndarray, context: SimulationContext) -> None:
        # Get the node indices
        n1 = self.Nodes[0].Index
        n2 = self.Nodes[1].Index

        # Calculate conductance (inverse of resistance)
        G = 1.0 / self._Resistance

        if n1 and n2:
            # Update the matrix A and vector b
            A[n1, n1] += G
            A[n1, n2] -= G
            A[n2, n1] -= G
            A[n2, n2] += G
        
        # If one of the nodes is ground (index None), we only update the diagonal element for the other node
        elif n1 and not n2: A[n1, n1] += G
        elif not n1 and n2: A[n2, n2] += G
    
    def UpdateState(self, solutionVector: np.ndarray, context: SimulationContext) -> None: pass
    
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        # Get the node indices
        n1 = self.Nodes[0].Index
        n2 = self.Nodes[1].Index

        # Calculate voltage difference across the resistor
        V1 = solutionVector[n1] if n1 else 0.0
        V2 = solutionVector[n2] if n2 else 0.0
        voltage_diff = V1 - V2

        # Calculate current using Ohm's Law: I = V / R
        current = voltage_diff / self._Resistance
        return current

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        # Get the node indices
        n1 = self.Nodes[0].Index
        n2 = self.Nodes[1].Index

        # Calculate voltage difference across the resistor
        V1 = solutionVector[n1] if n1 else 0.0
        V2 = solutionVector[n2] if n2 else 0.0
        voltage_diff = V1 - V2

        return voltage_diff