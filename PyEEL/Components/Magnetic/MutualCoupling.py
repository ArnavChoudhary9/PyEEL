"""
Magnetic coupling between two independent inductors.

Models the mutual inductance ``M = k √(L₁ L₂)`` between two
:class:`Inductor` instances with coupling coefficient ``k`` (|k| < 1).
"""

from __future__ import annotations

import math
import numpy as np

from ...Core.Node import Node
from ...Core.NodeManager import NodeManager
from ...Core.SimulationContext import SimulationContext, SimulationMode
from ..Component import Component
from ..Passive.Inductor import Inductor
from ..stamp_helpers import stamp_conductance, stamp_transconductance


class MutualCoupling(Component):
    """
    Magnetic coupling between two independent inductors.

    Parameters
    ----------
    name : str
        Component identifier (e.g. ``'K1'``).
    inductor1 : Inductor
        First coupled inductor.
    inductor2 : Inductor
        Second coupled inductor.
    k : float
        Coupling coefficient, must satisfy ``|k| < 1``.
    """

    _L1: Inductor
    _L2: Inductor
    _k: float
    _M: float
    _i1_prev: float
    _i2_prev: float

    def __init__(self, name: str, inductor1: Inductor,
                 inductor2: Inductor, k: float):
        if not isinstance(inductor1, Inductor):
            raise TypeError(
                f"MutualCoupling '{name}': inductor1 must be an Inductor, "
                f"got {type(inductor1).__name__}."
            )
        if not isinstance(inductor2, Inductor):
            raise TypeError(
                f"MutualCoupling '{name}': inductor2 must be an Inductor, "
                f"got {type(inductor2).__name__}."
            )
        if inductor1 is inductor2:
            raise ValueError(
                f"MutualCoupling '{name}': cannot couple an inductor to itself."
            )
        if abs(k) > 1.0:
            raise ValueError(
                f"MutualCoupling '{name}': |k| must be ≤ 1, got {k}."
            )
        if abs(k) == 1.0:
            raise ValueError(
                f"MutualCoupling '{name}': |k| = 1 causes a singular "
                f"conductance matrix (D = L₁L₂ - M² = 0). Use |k| < 1."
            )

        M_candidate = k * math.sqrt(inductor1.Inductance * inductor2.Inductance)
        M_limit = math.sqrt(inductor1.Inductance * inductor2.Inductance)
        if abs(M_candidate) > M_limit * (1.0 + 1e-12):
            raise ValueError(
                f"MutualCoupling '{name}': |M| = {abs(M_candidate):.6e} H "
                f"exceeds √(L₁L₂) = {M_limit:.6e} H. "
                f"This is non-physical."
            )

        all_nodes = list(inductor1.Nodes) + list(inductor2.Nodes)
        unique_nodes = tuple(dict.fromkeys(all_nodes))

        super().__init__(name, unique_nodes)

        self._L1 = inductor1
        self._L2 = inductor2
        self._k = k
        self._M = k * math.sqrt(inductor1.Inductance * inductor2.Inductance)
        self._i1_prev = 0.0
        self._i2_prev = 0.0

    # ── properties ──────────────────────────────────────────────────
    @property
    def CouplingCoefficient(self) -> float:
        return self._k

    @property
    def MutualInductance(self) -> float:
        return self._M

    @property
    def Inductor1(self) -> Inductor:
        return self._L1

    @property
    def Inductor2(self) -> Inductor:
        return self._L2

    # ── MNA interface ───────────────────────────────────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        pass

    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        if context.Mode == SimulationMode.DC:
            return

        dt = context.dt
        L1_val = self._L1.Inductance
        L2_val = self._L2.Inductance
        M = self._M
        D = L1_val * L2_val - M * M

        G11 = dt * L2_val / D
        G22 = dt * L1_val / D
        G12 = -dt * M / D

        G1_self = dt / L1_val
        G2_self = dt / L2_val

        dG1 = G11 - G1_self
        dG2 = G22 - G2_self

        n1p = self._L1.Nodes[0].Index
        n1n = self._L1.Nodes[1].Index
        n2p = self._L2.Nodes[0].Index
        n2n = self._L2.Nodes[1].Index

        # Self-correction stamps
        stamp_conductance(A, n1p, n1n, dG1)
        stamp_conductance(A, n2p, n2n, dG2)

        # Cross-coupling stamps
        stamp_transconductance(A, n1p, n1n, n2p, n2n, G12)
        stamp_transconductance(A, n2p, n2n, n1p, n1n, G12)

        # RHS history-current corrections
        di1 = self._i1_prev - self._L1.PreviousCurrent
        if n1p is not None:
            b[n1p] -= di1
        if n1n is not None:
            b[n1n] += di1

        di2 = self._i2_prev - self._L2.PreviousCurrent
        if n2p is not None:
            b[n2p] -= di2
        if n2n is not None:
            b[n2n] += di2

    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        if context.Mode == SimulationMode.DC:
            self._i1_prev = self._L1.Current
            self._i2_prev = self._L2.Current
            return

        dt = context.dt
        L1_val = self._L1.Inductance
        L2_val = self._L2.Inductance
        M = self._M
        D = L1_val * L2_val - M * M

        G11 = dt * L2_val / D
        G22 = dt * L1_val / D
        G12 = -dt * M / D

        v1 = self._L1.GetVoltage(solutionVector)
        v2 = self._L2.GetVoltage(solutionVector)

        i1_new = G11 * v1 + G12 * v2 + self._i1_prev
        i2_new = G12 * v1 + G22 * v2 + self._i2_prev

        self._i1_prev = i1_new
        self._i2_prev = i2_new

        self._L1.PreviousCurrent = i1_new
        self._L1.Current = i1_new
        self._L2.PreviousCurrent = i2_new
        self._L2.Current = i2_new

    # ── query helpers ───────────────────────────────────────────────
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        return 0.0

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        return 0.0

    def GetInductorCurrents(self, solutionVector: np.ndarray) -> tuple[float, float]:
        """Return ``(i1, i2)`` — the correct coupled inductor currents."""
        return (self._L1.Current, self._L2.Current)
