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

        The returned value is multiplied by ``context.source_factor``
        (default 1.0).  During *source stepping* — a convergence aid
        for difficult DC operating-point problems — the factor ramps
        from 0 → 1 so that sources are gradually turned on.
        """
        if context.Mode == SimulationMode.TRANSIENT:
            raw = self._Waveform(context)
        elif context.Mode == SimulationMode.DC:
            raw = self._Waveform.DCValue
        else:
            raw = self._Waveform.StaticValue

        return raw * context.source_factor