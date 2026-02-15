from ..SimulationContext import SimulationContext
from ..NodeManager import *

from abc import ABC, abstractmethod
import numpy as np 

class Component(ABC):
    _Name: str
    _Nodes: tuple[Node, ...] # Current flows from the first node to the second node, etc.
    _aux_indices: list[int]
    _state: dict[str, float]
    
    def __init__(self, name: str, nodes: tuple[Node, ...], aux_indices: list[int] = []):
        self._Name = name
        self._Nodes = nodes
        self._aux_indices = aux_indices
        self._state = {}
        
        # Raise an error if nodes are same
        if len(set(nodes)) != len(nodes):
            raise ValueError(f"Component {name} has duplicate nodes.")
        
        # Raise an error if nodes are empty
        if not nodes:
            raise ValueError(f"Component {name} must have at least one node.")      
    
    @property
    def Name(self) -> str: return self._Name
    @property
    def Nodes(self) -> tuple[Node, ...]: return self._Nodes
    @property
    def AuxIndices(self) -> list[int]: return self._aux_indices
    @property
    def PreviousState(self) -> dict[str, float]: return self._state
    
    @abstractmethod
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None: ...
    
    @abstractmethod
    def Stamp(self, A: np.ndarray, b: np.ndarray, context: SimulationContext) -> None: ...
    
    @abstractmethod
    def UpdateState(self, solutionVector: np.ndarray, context: SimulationContext) -> None: ...
    
    @abstractmethod
    def GetCurrent(self, solutionVector: np.ndarray) -> float: ...
    
    @abstractmethod
    def GetVoltage(self, solutionVector: np.ndarray) -> float: ...
