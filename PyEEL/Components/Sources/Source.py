from .Waveform import Waveform
from ..Component import Component
from ...SimulationContext import SimulationContext, SimulationMode
from ...Node import Node

from abc import ABC


class Source(Component, ABC):
    """
    Abstract base class for independent sources (voltage or current).

    Wraps a :class:`Waveform` to provide a time-varying or constant
    excitation value that subclasses stamp into the MNA system.
    """

    _Waveform: Waveform

    def __init__(self, name: str, nodes: tuple[Node, ...], waveform: Waveform):
        super().__init__(name, nodes)
        self._Waveform = waveform

    def EvaluateWaveform(self, context: SimulationContext) -> float:
        """
        Return the source value for the current simulation context.

        * **TRANSIENT** — waveform evaluated at ``context.Time``.
        * **DC** — returns the waveform's DC component (offset).
        * **AC** — returns the peak / static value.
        """
        if context.Mode == SimulationMode.TRANSIENT:
            return self._Waveform(context)
        if context.Mode == SimulationMode.DC:
            return self._Waveform.DCValue
        return self._Waveform.StaticValue