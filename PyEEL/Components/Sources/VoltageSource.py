from .Source import Source
from .Waveform import Waveform, ConstantWave, SineWave
from ...Node import Node
from ...NodeManager import NodeManager
from ...SimulationContext import SimulationContext

import numpy as np

class VoltageSource(Source):
    def __init__(self, name: str, nodes: tuple[Node, Node], waveform: Waveform):
        super().__init__(name, nodes, waveform)
        
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        self._aux_indices.append(nodeManager.RequestAuxiliaryUnknown())
        
    def Stamp(self, A: np.ndarray, b: np.ndarray, context: SimulationContext) -> None:
        n1, n2 = self.Nodes
        aux_index = self.AuxIndices[0]
        
        if n1.Index:
            A[aux_index, n1.Index] = 1
            A[n1.Index, aux_index] = 1
            
        if n2.Index:
            A[aux_index, n2.Index] = -1
            A[n2.Index, aux_index] = -1
            
        b[aux_index] = self.EvaluateWaveform(context)
        
    def UpdateState(self, solutionVector: np.ndarray, context: SimulationContext) -> None: pass
    
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        aux_index = self.AuxIndices[0]
        return solutionVector[aux_index]
    
    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        n1, n2 = self.Nodes
        v1 = solutionVector[n1.Index] if n1.Index else 0
        v2 = solutionVector[n2.Index] if n2.Index else 0
        return v1 - v2

# Common voltage source generators
DCVoltageSource = lambda name, nodes, voltage: VoltageSource(name, nodes, ConstantWave(voltage))
ACVoltageSource = lambda name, nodes, amplitude, frequency: VoltageSource(name, nodes, SineWave(amplitude, frequency))
