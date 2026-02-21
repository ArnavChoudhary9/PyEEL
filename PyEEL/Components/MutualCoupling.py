from __future__ import annotations

from ..Node import Node
from ..NodeManager import NodeManager
from ..SimulationContext import SimulationContext
from .Component import Component
from .Inductor import Inductor

import math
import numpy as np


class MutualCoupling(Component):
    """
    Magnetic coupling between two independent inductors.

    Models the mutual inductance **M = k √(L₁ L₂)** between *inductor1*
    and *inductor2* with coupling coefficient *k*  (``|k| < 1``).

    Coupled constitutive relation (backward-Euler discretised)::

        ⎡i₁⎤       dt      ⎡ L₂  -M⎤ ⎡v₁⎤   ⎡i₁_prev⎤
        ⎢  ⎥ = ——————————— ⎢       ⎥·⎢  ⎥ + ⎢       ⎥
        ⎣i₂⎦   L₁L₂ - M²   ⎣-M   L₁⎦ ⎣v₂⎦   ⎣i₂_prev⎦

    The two inductors keep their own independent conductance stamps
    (``G = dt/L``).  This component adds:

    * **Self-correction stamps** — adjusts each inductor's self-
      conductance from ``dt/L`` to the correct coupled value.
    * **Cross-coupling stamps** — a 2x2 transconductance cross-block
      linking the node-pairs of the two inductors.
    * **RHS history-current corrections** — compensates for any
      difference between the coupling's tracked branch currents and
      the inductors' own stored history.

    After each time-step the coupling overwrites both inductors'
    internal current state with the correct coupled values so that
    ``Inductor.GetCurrent()`` and subsequent stamps remain consistent.

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
        ``k > 0`` for aiding coupling, ``k < 0`` for opposing.
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

        # Collect unique nodes (preserving order, removing duplicates
        # that arise when inductors share a node).
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
        """Coupling coefficient *k* (dimensionless)."""
        return self._k

    @property
    def MutualInductance(self) -> float:
        """Mutual inductance *M* in henrys (H)."""
        return self._M

    @property
    def Inductor1(self) -> Inductor:
        """First coupled inductor."""
        return self._L1

    @property
    def Inductor2(self) -> Inductor:
        """Second coupled inductor."""
        return self._L2

    # ── MNA interface ───────────────────────────────────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        """No auxiliary unknowns — coupling is expressed via conductances."""
        pass

    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        """
        Stamp coupling corrections into the MNA system.

        Three groups of entries are added:

        1. **Self-correction** — adjusts each inductor's diagonal
           conductance from ``dt/L`` to ``dt·L_other / D``.
        2. **Cross-block** — 2x2 transconductance linking the two
           inductor node-pairs with ``G₁₂ = G₂₁ = -dt·M / D``.
        3. **RHS history** — corrects the history-current source in
           **b** whenever the coupling's tracked ``i_prev`` differs
           from the inductor's own stored value.
        """
        dt = context.dt
        L1_val = self._L1.Inductance
        L2_val = self._L2.Inductance
        M = self._M
        D = L1_val * L2_val - M * M

        # ── coupled conductance entries ─────────────────────────────
        G11 = dt * L2_val / D          # correct self-conductance for L1
        G22 = dt * L1_val / D          # correct self-conductance for L2
        G12 = -dt * M / D              # cross-conductance (= G21)

        # ── independent self-conductances (already stamped by each L)
        G1_self = dt / L1_val
        G2_self = dt / L2_val

        # ── corrections ────────────────────────────────────────────
        dG1 = G11 - G1_self            # = dt · M² / (L1 · D)
        dG2 = G22 - G2_self            # = dt · M² / (L2 · D)

        # Node indices
        n1p = self._L1.Nodes[0].Index
        n1n = self._L1.Nodes[1].Index
        n2p = self._L2.Nodes[0].Index
        n2n = self._L2.Nodes[1].Index

        # ── 1. self-correction stamps ───────────────────────────────
        _stamp_conductance(A, n1p, n1n, dG1)
        _stamp_conductance(A, n2p, n2n, dG2)

        # ── 2. cross-coupling stamps (2×2 cross-block) ─────────────
        #   i1 ← G12 · v2   and   i2 ← G12 · v1
        _stamp_transconductance(A, n1p, n1n, n2p, n2n, G12)
        _stamp_transconductance(A, n2p, n2n, n1p, n1n, G12)

        # ── 3. RHS history-current corrections ──────────────────────
        #   Difference between the correct (coupled) i_prev tracked
        #   here and the (uncoupled) value the inductor stamped.
        di1 = self._i1_prev - self._L1._i_prev
        if n1p is not None:
            b[n1p] -= di1
        if n1n is not None:
            b[n1n] += di1

        di2 = self._i2_prev - self._L2._i_prev
        if n2p is not None:
            b[n2p] -= di2
        if n2n is not None:
            b[n2n] += di2

    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        """
        Compute the correct coupled inductor currents and update both
        the coupling's own history and the inductors' internal state.
        """
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

        # Store for next step's history term
        self._i1_prev = i1_new
        self._i2_prev = i2_new

        # Override inductor internal state so that GetCurrent() and
        # the next step's independent history stamps stay consistent.
        self._L1._i_prev = i1_new
        self._L1._current = i1_new
        self._L2._i_prev = i2_new
        self._L2._current = i2_new

    # ── query helpers ───────────────────────────────────────────────
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """
        Not physically meaningful for a coupling element.

        Returns ``0.0``.  Use ``Inductor1.GetCurrent()`` or
        ``Inductor2.GetCurrent()`` for branch currents.
        """
        return 0.0

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """
        Not physically meaningful for a coupling element.

        Returns ``0.0``.
        """
        return 0.0

    def GetInductorCurrents(
        self, solutionVector: np.ndarray          # noqa: ARG002
    ) -> tuple[float, float]:
        """Return ``(i1, i2)`` — the correct coupled inductor currents."""
        return (self._L1._current, self._L2._current)


# ═══════════════════════════════════════════════════════════════════
#  Module-level stamp helpers (shared with potential future components)
# ═══════════════════════════════════════════════════════════════════

def _stamp_conductance(A: np.ndarray, na, nb, G: float) -> None:
    """Stamp conductance *G* between node indices *na* and *nb*."""
    if na is not None and nb is not None:
        A[na, na] += G;  A[na, nb] -= G
        A[nb, na] -= G;  A[nb, nb] += G
    elif na is not None:
        A[na, na] += G
    elif nb is not None:
        A[nb, nb] += G


def _stamp_transconductance(A: np.ndarray,
                            n_out_p, n_out_n,
                            n_in_p, n_in_n,
                            Gm: float) -> None:
    """
    Stamp a voltage-controlled current source (transconductance).

    Current ``Gm · (V(n_in_p) - V(n_in_n))`` flows from *n_out_p*
    toward *n_out_n*.
    """
    if n_out_p is not None:
        if n_in_p is not None:
            A[n_out_p, n_in_p] += Gm
        if n_in_n is not None:
            A[n_out_p, n_in_n] -= Gm
    if n_out_n is not None:
        if n_in_p is not None:
            A[n_out_n, n_in_p] -= Gm
        if n_in_n is not None:
            A[n_out_n, n_in_n] += Gm
