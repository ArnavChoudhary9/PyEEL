"""
Ideal linear resistor.

Ohm's law:  ``V = I · R``  →  conductance stamp ``G = 1/R``.
"""

from __future__ import annotations

import numpy as np

from ...Core.Node import Node
from ...Core.NodeManager import NodeManager
from ...Core.SimulationContext import SimulationContext
from ..Component import Component
from ..stamp_helpers import stamp_conductance, get_voltage_across


class Resistor(Component):
    """
    Ideal linear resistor.

    Convention: current flows from ``Nodes[0]`` to ``Nodes[1]``.
    """

    _Resistance: float

    def __init__(self, name: str, nodes: tuple[Node, Node], resistance: float):
        if resistance <= 0:
            raise ValueError(
                f"Resistor '{name}': resistance must be positive, got {resistance}."
            )
        super().__init__(name, nodes)
        self._Resistance = resistance
        self._Conductance = 1.0 / resistance

    @property
    def Resistance(self) -> float:
        """Resistance in ohms (Ω)."""
        return self._Resistance

    @Resistance.setter
    def Resistance(self, value: float) -> None:
        self._Resistance = value
        self._Conductance = 1.0 / value

    # ── MNA interface ───────────────────────────────────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        pass

    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        stamp_conductance(A, self.Nodes[0].Index, self.Nodes[1].Index,
                          self._Conductance)

    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        pass

    # ── query helpers ───────────────────────────────────────────────
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        return self.GetVoltage(solutionVector) / self._Resistance

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        return get_voltage_across(solutionVector,
                                  self.Nodes[0].Index, self.Nodes[1].Index)
