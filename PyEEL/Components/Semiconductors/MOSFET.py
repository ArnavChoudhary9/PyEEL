"""
Level-1 (Shichman-Hodges) MOSFET model.

Implements NMOS and PMOS enhancement-mode MOSFETs as nonlinear
three-terminal components.

Terminals: ``(drain, gate, source)``

Current convention: ``I_d`` flows from drain to source (NMOS) or
source to drain (PMOS — handled by polarity flip).
"""

from __future__ import annotations

import math
from enum import Enum
import numpy as np

from ...Core.Node import Node
from ...Core.NodeManager import NodeManager
from ...Core.SimulationContext import SimulationContext, SimulationMode
from ..Component import Component


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
        Transconductance parameter (A/V²).  Default ``2e-5``.
    Vth : float
        Threshold voltage (V).  Default ``1.0``.
    lambda_ : float
        Channel-length modulation parameter (1/V).  Default ``0.0``.
    """

    _Kp: float
    _Vth: float
    _lambda: float
    _type: MOSFETType
    _polarity: int

    _id_prev: float
    _vgs_prev: float
    _vds_prev: float

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
        self._polarity = mosfet_type.value

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
        pass

    # ── helpers ─────────────────────────────────────────────────────
    def _node_voltage(self, solutionVector: np.ndarray | None, idx: int) -> float:
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
        """Evaluate drain current, gm, gds.  Returns ``(Id, gm, gds)``."""
        Kp = self._Kp
        Vth = self._Vth
        lam = self._lambda
        Vov = Vgs - Vth

        if Vov <= 0:
            Id = 0.0
            gm = 0.0
            gds = 0.0
        else:
            if Vds < 0:
                Vds = 0.0

            if Vds < Vov:
                # Linear / triode
                Id = Kp * (Vov * Vds - 0.5 * Vds * Vds) * (1.0 + lam * Vds)
                gm = Kp * Vds * (1.0 + lam * Vds)
                gds = Kp * ((Vov - Vds) * (1.0 + lam * Vds)
                            + lam * (Vov * Vds - 0.5 * Vds * Vds))
            else:
                # Saturation
                Id = 0.5 * Kp * Vov * Vov * (1.0 + lam * Vds)
                gm = Kp * Vov * (1.0 + lam * Vds)
                gds = 0.5 * Kp * Vov * Vov * lam

        gm = max(gm, self._G_MIN)
        gds = max(gds, self._G_MIN)

        return Id, gm, gds

    # ── stamp ───────────────────────────────────────────────────────
    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        if context.x_current is not None:
            Vgs0, Vds0 = self._get_voltages(context.x_current)
        else:
            Vgs0 = self._vgs_prev
            Vds0 = self._vds_prev

        Id0, gm, gds = self._evaluate(Vgs0, Vds0)

        Ieq = Id0 - gm * Vgs0 - gds * Vds0

        d = self.Nodes[0].Index   # drain
        g = self.Nodes[1].Index   # gate
        s = self.Nodes[2].Index   # source
        p = self._polarity

        # gm stamp (Vgs-controlled current into drain, out of source)
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

        # gds stamp (resistor d↔s)
        if d is not None and s is not None:
            A[d, d] += gds
            A[d, s] -= gds
            A[s, d] -= gds
            A[s, s] += gds
        elif d is not None:
            A[d, d] += gds
        elif s is not None:
            A[s, s] += gds

        # Current-source Ieq
        Ieq_phys = p * Ieq
        if d is not None:
            b[d] -= Ieq_phys
        if s is not None:
            b[s] += Ieq_phys

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
        return self._polarity * self._id_prev

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
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
