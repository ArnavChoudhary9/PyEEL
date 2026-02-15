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

        In transient mode the waveform is evaluated at ``context.Time``;
        for DC/AC the static (peak) value is returned.
        """
        if context.Mode == SimulationMode.TRANSIENT:
            return self._Waveform(context)
        return self._Waveform.StaticValue