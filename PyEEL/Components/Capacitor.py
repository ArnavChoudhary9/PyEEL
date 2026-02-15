from ..Node import Node
from ..NodeManager import NodeManager
from ..SimulationContext import SimulationContext
from .Component import Component

import numpy as np


class Capacitor(Component):
    """
    Ideal linear capacitor.

    Constitutive relation:  ``i = C · dv/dt``

    Discretised with backward Euler the capacitor becomes an equivalent
    conductance ``G_eq = C / dt`` in parallel with a history current
    source ``I_hist = G_eq · v_prev``.

    Convention: current flows from ``Nodes[0]`` to ``Nodes[1]``.
    """

    _Capacitance: float

    def __init__(self, name: str, nodes: tuple[Node, Node], capacitance: float):
        if capacitance <= 0:
            raise ValueError(
                f"Capacitor '{name}': capacitance must be positive, got {capacitance}."
            )
        super().__init__(name, nodes)
        self._Capacitance = capacitance

    @property
    def Capacitance(self) -> float:
        """Capacitance in farads (F)."""
        return self._Capacitance

    # ── MNA interface ───────────────────────────────────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        """Capacitors introduce no auxiliary unknowns."""
        pass

    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        """
        Stamp the backward-Euler companion model into the MNA system.

        Equivalent conductance ``G_eq = C / dt`` is stamped like a
        resistor.  The history current source
        ``I_hist = G_eq · v_prev_across`` is added to the **b** vector.
        """
        n1 = self.Nodes[0].Index
        n2 = self.Nodes[1].Index
        G_eq = self._Capacitance / context.dt

        # ── conductance stamp (identical to a resistor with G_eq) ───
        if n1 is not None and n2 is not None:
            A[n1, n1] += G_eq
            A[n1, n2] -= G_eq
            A[n2, n1] -= G_eq
            A[n2, n2] += G_eq
        elif n1 is not None:
            A[n1, n1] += G_eq
        elif n2 is not None:
            A[n2, n2] += G_eq

        # ── history current source ──────────────────────────────────
        v_prev = self._state.get("v_prev", 0.0)
        I_hist = G_eq * v_prev

        if n1 is not None:
            b[n1] += I_hist
        if n2 is not None:
            b[n2] -= I_hist

    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        """Store voltage across the capacitor for the next time-step."""
        v = self.GetVoltage(solutionVector)
        v_prev = self._state.get("v_prev", 0.0)
        G_eq = self._Capacitance / context.dt
        self._state["current"] = G_eq * (v - v_prev)
        self._state["v_prev"] = v

    # ── query helpers ───────────────────────────────────────────────
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """Return current through the capacitor (computed during UpdateState)."""
        return self._state.get("current", 0.0)

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return voltage drop ``V(n1) - V(n2)``."""
        n1 = self.Nodes[0].Index
        n2 = self.Nodes[1].Index
        V1 = solutionVector[n1] if n1 is not None else 0.0
        V2 = solutionVector[n2] if n2 is not None else 0.0
        return float(V1 - V2)
