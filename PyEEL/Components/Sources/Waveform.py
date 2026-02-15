from ...SimulationContext import SimulationContext

import math
from abc import ABC, abstractmethod

class Waveform(ABC):
    @abstractmethod
    def GetValue(self, context: SimulationContext) -> float: ...
    
    @property
    @abstractmethod
    def StaticValue(self) -> float: ...
    
    def __call__(self, context: SimulationContext) -> float:
        return self.GetValue(context)
    
# Common waveforms
class ConstantWave(Waveform):
    def __init__(self, value: float):
        self._Value = value
    
    def GetValue(self, context: SimulationContext) -> float:
        return self._Value
    
    @property
    def StaticValue(self) -> float: return self._Value

class SineWave(Waveform):
    def __init__(self, frequency: float, amplitude: float = 1.0, phase: float = 0.0):
        self._Frequency = frequency
        self._Amplitude = amplitude
        self._Phase = phase
    
    def GetValue(self, context: SimulationContext) -> float:
        return self._Amplitude * math.sin(2 * math.pi * self._Frequency * context.Time + self._Phase)
    
    @property
    def StaticValue(self) -> float: return self._Amplitude
