from ...SimulationContext import SimulationContext

import math
from abc import ABC, abstractmethod


class Waveform(ABC):
    """
    Abstract time-domain waveform.

    Subclass this to define arbitrary excitation shapes.  Every waveform
    must provide:

    * :meth:`GetValue` — instantaneous value given a simulation context.
    * :attr:`StaticValue` — the representative DC / peak value.
    """

    @abstractmethod
    def GetValue(self, context: SimulationContext) -> float:
        """Return the waveform value at ``context.Time``."""
        ...

    @property
    @abstractmethod
    def StaticValue(self) -> float:
        """DC or peak value used for non-transient analyses."""
        ...

    def __call__(self, context: SimulationContext) -> float:
        return self.GetValue(context)


# ── built-in waveforms ────────────────────────────────────────────
class ConstantWave(Waveform):
    """Time-invariant constant value (DC)."""

    def __init__(self, value: float):
        self._Value = value

    def GetValue(self, context: SimulationContext) -> float:
        return self._Value

    @property
    def StaticValue(self) -> float:
        return self._Value


class SineWave(Waveform):
    """
    Sinusoidal waveform: ``A · sin(2π f t + φ)``.

    Parameters
    ----------
    frequency : float
        Frequency in Hz.
    amplitude : float
        Peak amplitude.
    phase : float
        Phase offset in radians.
    """

    def __init__(self, frequency: float, amplitude: float = 1.0,
                 phase: float = 0.0):
        self._Frequency = frequency
        self._Amplitude = amplitude
        self._Phase = phase

    def GetValue(self, context: SimulationContext) -> float:
        return self._Amplitude * math.sin(
            2 * math.pi * self._Frequency * context.Time + self._Phase
        )

    @property
    def StaticValue(self) -> float:
        return self._Amplitude
