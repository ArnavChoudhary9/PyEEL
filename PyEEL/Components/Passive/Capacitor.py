"""
Ideal linear capacitor.

Constitutive relation: ``i = C · dv/dt``

Discretised with backward Euler the capacitor becomes an equivalent
conductance ``G_eq = C / dt`` in parallel with a history current
source ``I_hist = G_eq · v_prev``.
"""

from __future__ import annotations

import numpy as np

from ...Core.Node import Node
from ...Core.NodeManager import NodeManager
from ...Core.SimulationContext import SimulationContext, SimulationMode
from ..Component import Component
from ..stamp_helpers import stamp_conductance, stamp_current_source, get_voltage_across


class Capacitor(Component):
    """
    Ideal linear capacitor.

    Convention: current flows from ``Nodes[0]`` to ``Nodes[1]``.
    """

    _Capacitance: float

    def __init__(self, name: str, nodes: tuple[Node, Node], capacitance: float,
                 *, initial_voltage: float | None = None):
        if capacitance <= 0:
            raise ValueError(
                f"Capacitor '{name}': capacitance must be positive, got {capacitance}."
            )
        super().__init__(name, nodes)
        self._Capacitance = capacitance
        self._initial_voltage = initial_voltage
        self._v_prev = initial_voltage if initial_voltage is not None else 0.0
        self._current = 0.0

    @property
    def Capacitance(self) -> float:
        """Capacitance in farads (F)."""
        return self._Capacitance

    @property
    def InitialVoltage(self) -> float | None:
        """User-specified initial voltage (V), or ``None``."""
        return self._initial_voltage

    # ── MNA interface ───────────────────────────────────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        pass

    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        # DC operating point: capacitor is an open circuit
        if context.Mode == SimulationMode.DC:
            return

        n1 = self.Nodes[0].Index
        n2 = self.Nodes[1].Index
        G_eq = self._Capacitance / context.dt

        # Conductance stamp
        stamp_conductance(A, n1, n2, G_eq)

        # History current source: I_hist = G_eq * v_prev
        I_hist = G_eq * self._v_prev
        if n1 is not None:
            b[n1] += I_hist
        if n2 is not None:
            b[n2] -= I_hist

    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        v = self.GetVoltage(solutionVector)

        if context.Mode == SimulationMode.DC:
            self._v_prev = v
            self._current = 0.0
            return

        G_eq = self._Capacitance / context.dt
        self._current = G_eq * (v - self._v_prev)
        self._v_prev = v

    # ── query helpers ───────────────────────────────────────────────
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        return self._current

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        return get_voltage_across(solutionVector,
                                  self.Nodes[0].Index, self.Nodes[1].Index)
