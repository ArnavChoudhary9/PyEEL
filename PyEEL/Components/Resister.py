from ..Node import Node
from ..NodeManager import NodeManager
from ..SimulationContext import SimulationContext
from .Component import Component

import numpy as np


class Resister(Component):
    """
    Ideal linear resistor.

    Ohm's law:  ``V = I · R``  →  conductance stamp ``G = 1/R``.

    Convention: current flows from ``Nodes[0]`` to ``Nodes[1]``.
    """

    _Resistance: float

    def __init__(self, name: str, nodes: tuple[Node, Node], resistance: float):
        if resistance <= 0:
            raise ValueError(
                f"Resister '{name}': resistance must be positive, got {resistance}."
            )
        super().__init__(name, nodes)
        self._Resistance = resistance

    @property
    def Resistance(self) -> float:
        """Resistance in ohms (Ω)."""
        return self._Resistance

    # ── MNA interface ───────────────────────────────────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        """Resistors introduce no auxiliary unknowns."""
        pass

    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        """
        Stamp the conductance ``G = 1/R`` into the MNA matrix.

        For nodes *n1* and *n2* the contribution is::

            A[n1,n1] += G    A[n1,n2] -= G
            A[n2,n1] -= G    A[n2,n2] += G

        When a terminal is ground (``Index is None``) the corresponding
        row/column is omitted (the ground node is the reference).
        """
        n1 = self.Nodes[0].Index
        n2 = self.Nodes[1].Index
        G = 1.0 / self._Resistance

        if n1 is not None and n2 is not None:
            A[n1, n1] += G
            A[n1, n2] -= G
            A[n2, n1] -= G
            A[n2, n2] += G
        elif n1 is not None:            # n2 is ground
            A[n1, n1] += G
        elif n2 is not None:            # n1 is ground
            A[n2, n2] += G

    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        """Resistors are memoryless — nothing to update."""
        pass

    # ── query helpers ───────────────────────────────────────────────
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """Return current through the resistor via Ohm's law ``I = V/R``."""
        return self.GetVoltage(solutionVector) / self._Resistance

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return voltage drop ``V(n1) − V(n2)``."""
        n1 = self.Nodes[0].Index
        n2 = self.Nodes[1].Index
        V1 = solutionVector[n1] if n1 is not None else 0.0
        V2 = solutionVector[n2] if n2 is not None else 0.0
        return V1 - V2