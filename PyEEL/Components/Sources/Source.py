from .Waveform import Waveform
from ..Component import Component
from ...SimulationContext import SimulationContext, SimulationMode
from ...Node import Node

from abc import ABC

class Source(Component, ABC):
    _Waveform: Waveform
    
    def __init__(self, name: str, nodes: tuple[Node, ...], waveform: Waveform):
        super().__init__(name, nodes)
        self._Waveform = waveform
        
    def EvaluateWaveform(self, context: SimulationContext) -> float:
        if context.Mode == SimulationMode.TRANSIENT:
            return self._Waveform(context)
        
        return self._Waveform.StaticValue