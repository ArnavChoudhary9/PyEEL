from ..Node import Node
from ..NodeManager import NodeManager
from ..SimulationContext import SimulationContext, SimulationMode
from .Component import Component

import numpy as np


class Inductor(Component):
    """
    Ideal linear inductor.

    Constitutive relation:  ``v = L · di/dt``

    Discretised with backward Euler the inductor becomes an equivalent
    conductance ``G_eq = dt / L`` in parallel with a history current
    source ``I_hist = i_prev``.

    Convention: current flows from ``Nodes[0]`` to ``Nodes[1]``.
    """

    _Inductance: float

    # ── DC short-circuit conductance ────────────────────────────────
    _DC_SHORT_RESISTANCE: float = 1e-9   # 1 nΩ — effectively a short

    def __init__(self, name: str, nodes: tuple[Node, Node], inductance: float):
        if inductance <= 0:
            raise ValueError(
                f"Inductor '{name}': inductance must be positive, got {inductance}."
            )
        super().__init__(name, nodes)
        self._Inductance = inductance
        self._i_prev = 0.0
        self._current = 0.0

    @property
    def Inductance(self) -> float:
        """Inductance in henrys (H)."""
        return self._Inductance

    # ── MNA interface ───────────────────────────────────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        """Inductors introduce no auxiliary unknowns (conductance model)."""
        pass

    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        """
        Stamp the backward-Euler companion model into the MNA system.

        In **DC mode** the inductor is modelled as a short circuit
        (very large conductance).

        In **TRANSIENT mode** an equivalent conductance ``G_eq = dt / L``
        is stamped like a resistor, and the history current source
        ``I_hist = i_prev`` is subtracted from **b**.
        """
        n1 = self.Nodes[0].Index
        n2 = self.Nodes[1].Index

        # ── DC mode: inductor = short circuit ───────────────────────
        if context.Mode == SimulationMode.DC:
            G_dc = 1.0 / self._DC_SHORT_RESISTANCE
            if n1 is not None and n2 is not None:
                A[n1, n1] += G_dc;  A[n1, n2] -= G_dc
                A[n2, n1] -= G_dc;  A[n2, n2] += G_dc
            elif n1 is not None:
                A[n1, n1] += G_dc
            elif n2 is not None:
                A[n2, n2] += G_dc
            return

        # ── TRANSIENT mode: backward-Euler companion ────────────────
        G_eq = context.dt / self._Inductance

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
        i_prev = self._i_prev

        if n1 is not None:
            b[n1] -= i_prev
        if n2 is not None:
            b[n2] += i_prev

    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        """Compute and store the inductor current for the next step."""
        v = self.GetVoltage(solutionVector)

        if context.Mode == SimulationMode.DC:
            # Current through the short-circuit resistance
            G_dc = 1.0 / self._DC_SHORT_RESISTANCE
            self._current = G_dc * v
            self._i_prev = self._current
            return

        G_eq = context.dt / self._Inductance
        i_new = G_eq * v + self._i_prev
        self._current = i_new
        self._i_prev = i_new

    # ── query helpers ───────────────────────────────────────────────
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """Return current through the inductor (computed during UpdateState)."""
        return self._current

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return voltage drop ``V(n1) - V(n2)``."""
        n1 = self.Nodes[0].Index
        n2 = self.Nodes[1].Index
        V1 = solutionVector[n1] if n1 is not None else 0.0
        V2 = solutionVector[n2] if n2 is not None else 0.0
        return float(V1 - V2)
