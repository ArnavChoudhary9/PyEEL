"""
Level-1 (Shichman-Hodges) MOSFET model.

Implements NMOS and PMOS enhancement-mode MOSFETs as nonlinear
three-terminal components.  During Newton-Raphson iteration the
device is linearised around the current operating point and stamped
as companion conductances + current sources.

Drain-current equations (NMOS, ``Vgs - Vth > 0``)
---------------------------------------------------
Cut-off (``Vgs - Vth ≤ 0``)::

    I_d = 0

Linear / triode (``Vds < Vgs - Vth``)::

    I_d = Kp · [(Vgs - Vth) · Vds - 0.5 · Vds²] · (1 + λ · Vds)

Saturation (``Vds ≥ Vgs - Vth``)::

    I_d = 0.5 · Kp · (Vgs - Vth)² · (1 + λ · Vds)

For **PMOS** all voltage polarities are reversed internally so the
same equations apply.

Terminals
---------
``Nodes = (drain, gate, source)``

Current convention: ``I_d`` flows from drain to source (NMOS) or
source to drain (PMOS — handled by polarity flip).

Companion-model stamping
------------------------
The drain current is a function of two independent voltages Vgs and
Vds.  The NR companion linearisation is::

    I_d ≈ I_d0 + g_m · δVgs + g_ds · δVds

where::

    g_m  = ∂I_d/∂Vgs   (transconductance)
    g_ds = ∂I_d/∂Vds   (output conductance)

These are stamped as a two-port conductance network plus an
equivalent current source.
"""

from __future__ import annotations

import math
from enum import Enum
import numpy as np

from ..Node import Node
from ..NodeManager import NodeManager
from ..SimulationContext import SimulationContext, SimulationMode
from .Component import Component


class MOSFETType(Enum):
    """NMOS or PMOS."""
    NMOS = 1
    PMOS = -1


class MOSFET(Component):
    """
    Level-1 (Shichman–Hodges) MOSFET.

    Parameters
    ----------
    name : str
        Component identifier (e.g. ``'M1'``).
    nodes : tuple[Node, Node, Node]
        ``(drain, gate, source)``
    mosfet_type : MOSFETType
        ``MOSFETType.NMOS`` or ``MOSFETType.PMOS``.
    Kp : float
        Transconductance parameter (A/V²).  Default ``2e-5``
        (≈ 20 µA/V² — a small-signal device).
    Vth : float
        Threshold voltage (V).  Default ``1.0`` (NMOS) / ``−1.0`` (PMOS).
        Always specified as a positive number for NMOS; the PMOS
        polarity inversion is handled automatically.
    lambda_ : float
        Channel-length modulation parameter (1/V).  Default ``0.0``
        (ideal — no CLM).
    """

    _Kp: float
    _Vth: float
    _lambda: float
    _type: MOSFETType
    _polarity: int          # +1 for NMOS, −1 for PMOS

    _id_prev: float         # last converged drain current
    _vgs_prev: float
    _vds_prev: float

    # Small conductance floor to keep the Jacobian non-singular when
    # the device is fully off.
    _G_MIN: float = 1e-12

    def __init__(
        self,
        name: str,
        nodes: tuple[Node, Node, Node],
        mosfet_type: MOSFETType = MOSFETType.NMOS,
        *,
        Kp: float = 2e-5,
        Vth: float = 1.0,
        lambda_: float = 0.0,
    ):
        if Kp <= 0:
            raise ValueError(f"MOSFET '{name}': Kp must be positive, got {Kp}")
        if Vth < 0:
            raise ValueError(f"MOSFET '{name}': Vth must be non-negative, got {Vth}")
        if lambda_ < 0:
            raise ValueError(f"MOSFET '{name}': lambda_ must be non-negative, got {lambda_}")
        if len(nodes) != 3:
            raise ValueError(f"MOSFET '{name}': requires exactly 3 nodes (drain, gate, source)")

        super().__init__(name, nodes)
        self._Kp = Kp
        self._Vth = Vth
        self._lambda = lambda_
        self._type = mosfet_type
        self._polarity = mosfet_type.value   # +1 NMOS, −1 PMOS

        self._id_prev = 0.0
        self._vgs_prev = 0.0
        self._vds_prev = 0.0

    # ── properties ──────────────────────────────────────────────────
    @property
    def IsNonlinear(self) -> bool:
        return True

    @property
    def Type(self) -> MOSFETType:
        return self._type

    @property
    def Kp(self) -> float:
        return self._Kp

    @property
    def Vth(self) -> float:
        return self._Vth

    # ── MNA interface ───────────────────────────────────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        """MOSFETs introduce no auxiliary unknowns."""
        pass

    # ── helpers ─────────────────────────────────────────────────────
    def _node_voltage(self, solutionVector: np.ndarray | None, idx: int) -> float:
        """Read a node voltage, returning 0 for ground."""
        if solutionVector is None:
            return 0.0
        node = self.Nodes[idx]
        return float(solutionVector[node.Index]) if node.Index is not None else 0.0

    def _get_voltages(self, x: np.ndarray | None) -> tuple[float, float]:
        """Return ``(Vgs, Vds)`` with PMOS polarity inversion applied."""
        vd = self._node_voltage(x, 0)
        vg = self._node_voltage(x, 1)
        vs = self._node_voltage(x, 2)

        p = self._polarity
        Vgs = p * (vg - vs)
        Vds = p * (vd - vs)
        return Vgs, Vds

    def _evaluate(self, Vgs: float, Vds: float) -> tuple[float, float, float]:
        """
        Evaluate drain current, transconductance, and output conductance.

        All values use the *internal* sign convention (positive Id means
        current flows drain→source for NMOS).

        Returns ``(Id, gm, gds)``.
        """
        Kp = self._Kp
        Vth = self._Vth
        lam = self._lambda

        Vov = Vgs - Vth  # overdrive voltage

        if Vov <= 0:
            # ── cut-off ─────────────────────────────────────────────
            Id = 0.0
            gm = 0.0
            gds = 0.0
        else:
            # Ensure Vds ≥ 0 (swap drain/source if needed)
            if Vds < 0:
                Vds = 0.0

            if Vds < Vov:
                # ── linear / triode ─────────────────────────────────
                Id = Kp * (Vov * Vds - 0.5 * Vds * Vds) * (1.0 + lam * Vds)
                # Partial derivatives
                gm = Kp * Vds * (1.0 + lam * Vds)
                gds = Kp * ((Vov - Vds) * (1.0 + lam * Vds)
                            + lam * (Vov * Vds - 0.5 * Vds * Vds))
            else:
                # ── saturation ──────────────────────────────────────
                Id = 0.5 * Kp * Vov * Vov * (1.0 + lam * Vds)
                gm = Kp * Vov * (1.0 + lam * Vds)
                gds = 0.5 * Kp * Vov * Vov * lam

        # Floor conductances to keep the Jacobian well-conditioned
        gm = max(gm, self._G_MIN)
        gds = max(gds, self._G_MIN)

        return Id, gm, gds

    # ── stamp ───────────────────────────────────────────────────────
    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        """
        Stamp the linearised MOSFET companion model.

        The drain current is::

            I_d ≈ I_d0 + g_m·(Vgs - Vgs0) + g_ds·(Vds - Vds0)

        which rearranges to a two-port conductance network plus a
        constant current source ``I_eq = I_d0 - g_m·Vgs0 - g_ds·Vds0``.
        """
        # --- operating point --------------------------------------------
        if context.x_current is not None:
            Vgs0, Vds0 = self._get_voltages(context.x_current)
        else:
            Vgs0 = self._vgs_prev
            Vds0 = self._vds_prev

        Id0, gm, gds = self._evaluate(Vgs0, Vds0)

        # Equivalent current source (positive = drain→source)
        Ieq = Id0 - gm * Vgs0 - gds * Vds0

        # Node indices (None = ground)
        d = self.Nodes[0].Index   # drain
        g = self.Nodes[1].Index   # gate
        s = self.Nodes[2].Index   # source

        p = self._polarity  # +1 NMOS, −1 PMOS

        # The physical current is  I_phys = p · (gm·Vgs + gds·Vds + Ieq)
        # where Vgs = p·(Vg − Vs) and Vds = p·(Vd − Vs).
        # After substitution the p factors cancel in the conductance
        # stamps (p² = 1), but the current source keeps its sign.

        # ── g_m stamp (Vgs-controlled current into drain, out of source) ─
        # I_gm enters drain, leaves source; controlled by (Vg − Vs).
        # d row: +gm at g, −gm at s
        # s row: −gm at g, +gm at s
        if d is not None:
            if g is not None:
                A[d, g] += gm
            if s is not None:
                A[d, s] -= gm
        if s is not None:
            if g is not None:
                A[s, g] -= gm
            if s is not None:
                A[s, s] += gm

        # ── g_ds stamp (Vds-controlled current, like a resistor d↔s) ─
        if d is not None and s is not None:
            A[d, d] += gds
            A[d, s] -= gds
            A[s, d] -= gds
            A[s, s] += gds
        elif d is not None:
            A[d, d] += gds
        elif s is not None:
            A[s, s] += gds

        # ── current-source Ieq (positive = into drain, out of source) ─
        Ieq_phys = p * Ieq
        if d is not None:
            b[d] -= Ieq_phys       # current leaving drain node
        if s is not None:
            b[s] += Ieq_phys       # current entering source node

    # ── state update ────────────────────────────────────────────────
    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        Vgs, Vds = self._get_voltages(solutionVector)
        Id, _, _ = self._evaluate(Vgs, Vds)
        self._vgs_prev = Vgs
        self._vds_prev = Vds
        self._id_prev = Id

    # ── query helpers ───────────────────────────────────────────────
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """Return drain current (A). Positive = drain→source for NMOS."""
        return self._polarity * self._id_prev

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return Vds (drain-to-source voltage)."""
        vd = self._node_voltage(solutionVector, 0)
        vs = self._node_voltage(solutionVector, 2)
        return vd - vs


# ── convenience factories ───────────────────────────────────────────
def NMOS(name: str, nodes: tuple[Node, Node, Node], *,
         Kp: float = 2e-5, Vth: float = 1.0,
         lambda_: float = 0.0) -> MOSFET:
    """Create an N-channel enhancement MOSFET."""
    return MOSFET(name, nodes, MOSFETType.NMOS,
                  Kp=Kp, Vth=Vth, lambda_=lambda_)


def PMOS(name: str, nodes: tuple[Node, Node, Node], *,
         Kp: float = 2e-5, Vth: float = 1.0,
         lambda_: float = 0.0) -> MOSFET:
    """Create a P-channel enhancement MOSFET."""
    return MOSFET(name, nodes, MOSFETType.PMOS,
                  Kp=Kp, Vth=Vth, lambda_=lambda_)
