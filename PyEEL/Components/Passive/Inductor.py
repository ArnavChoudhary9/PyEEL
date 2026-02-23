"""
Ideal linear inductor.

Constitutive relation: ``v = L · di/dt``

Discretised with backward Euler the inductor becomes an equivalent
conductance ``G_eq = dt / L`` in parallel with a history current
source ``I_hist = i_prev``.
"""

from __future__ import annotations

import numpy as np

from ...Core.Node import Node
from ...Core.NodeManager import NodeManager
from ...Core.SimulationContext import SimulationContext, SimulationMode
from ..Component import Component
from ..stamp_helpers import stamp_conductance, get_voltage_across


class Inductor(Component):
    """
    Ideal linear inductor.

    Convention: current flows from ``Nodes[0]`` to ``Nodes[1]``.
    """

    _Inductance: float

    # ── DC short-circuit conductance ────────────────────────────────
    _DC_SHORT_RESISTANCE: float = 1e-9  # 1 nΩ — effectively a short

    def __init__(self, name: str, nodes: tuple[Node, Node], inductance: float,
                 *, initial_current: float | None = None):
        if inductance <= 0:
            raise ValueError(
                f"Inductor '{name}': inductance must be positive, got {inductance}."
            )
        super().__init__(name, nodes)
        self._Inductance = inductance
        self._initial_current = initial_current
        self._i_prev = initial_current if initial_current is not None else 0.0
        self._current = self._i_prev

    @property
    def Inductance(self) -> float:
        """Inductance in henrys (H)."""
        return self._Inductance

    @property
    def InitialCurrent(self) -> float | None:
        """User-specified initial current (A), or ``None``."""
        return self._initial_current

    # ── MNA interface ───────────────────────────────────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        pass

    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        n1 = self.Nodes[0].Index
        n2 = self.Nodes[1].Index

        # DC mode: inductor = short circuit (large conductance)
        if context.Mode == SimulationMode.DC:
            G_dc = 1.0 / self._DC_SHORT_RESISTANCE
            stamp_conductance(A, n1, n2, G_dc)
            return

        # TRANSIENT mode: backward-Euler companion
        G_eq = context.dt / self._Inductance
        stamp_conductance(A, n1, n2, G_eq)

        # History current source
        i_prev = self._i_prev
        if n1 is not None:
            b[n1] -= i_prev
        if n2 is not None:
            b[n2] += i_prev

    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        v = self.GetVoltage(solutionVector)

        if context.Mode == SimulationMode.DC:
            G_dc = 1.0 / self._DC_SHORT_RESISTANCE
            self._current = G_dc * v
            self._i_prev = self._current
            return

        G_eq = context.dt / self._Inductance
        i_new = G_eq * v + self._i_prev
        self._current = i_new
        self._i_prev = i_new

    # ── public current properties (used by MutualCoupling) ─────────
    @property
    def Current(self) -> float:
        """Current inductor current (A)."""
        return self._current

    @Current.setter
    def Current(self, value: float) -> None:
        self._current = value

    @property
    def PreviousCurrent(self) -> float:
        """Previous step inductor current (A)."""
        return self._i_prev

    @PreviousCurrent.setter
    def PreviousCurrent(self, value: float) -> None:
        self._i_prev = value

    # ── query helpers ───────────────────────────────────────────────
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        return self._current

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        return get_voltage_across(solutionVector,
                                  self.Nodes[0].Index, self.Nodes[1].Index)
