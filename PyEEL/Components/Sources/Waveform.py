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

    @property
    def DCValue(self) -> float:
        """DC component of the waveform for operating-point analysis.

        Defaults to :attr:`StaticValue`.  Override in AC waveforms
        that have no DC offset (e.g. pure sine → 0)."""
        return self.StaticValue

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
    Sinusoidal waveform: ``A · sin(2π f t + φ) + offset``.

    Parameters
    ----------
    frequency : float
        Frequency in Hz.
    amplitude : float
        Peak amplitude.
    phase : float
        Phase offset in radians.
    dc_offset : float
        Constant DC offset added to the sinusoid.  Defaults to 0.
    """

    def __init__(self, frequency: float, amplitude: float = 1.0,
                 phase: float = 0.0, dc_offset: float = 0.0):
        self._Frequency = frequency
        self._Amplitude = amplitude
        self._Phase = phase
        self._DCOffset = dc_offset

    def GetValue(self, context: SimulationContext) -> float:
        return self._DCOffset + self._Amplitude * math.sin(
            2 * math.pi * self._Frequency * context.Time + self._Phase
        )

    @property
    def StaticValue(self) -> float:
        return self._Amplitude

    @property
    def DCValue(self) -> float:
        """Pure sine has zero DC component (unless dc_offset is set)."""
        return self._DCOffset
