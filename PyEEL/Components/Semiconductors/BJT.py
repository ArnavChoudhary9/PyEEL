"""
Ebers–Moll BJT model (NPN / PNP).

Implements bipolar junction transistors as nonlinear three-terminal
components.  The device is decomposed into BE/BC junction diodes
and forward/reverse transport current sources, each linearised
during Newton-Raphson iteration.

Terminals: ``(collector, base, emitter)``
"""

from __future__ import annotations

import math
from enum import Enum
import numpy as np

from ...Core.Node import Node
from ...Core.NodeManager import NodeManager
from ...Core.SimulationContext import SimulationContext, SimulationMode
from ..Component import Component


class BJTType(Enum):
    """NPN or PNP."""
    NPN = 1
    PNP = -1


class BJT(Component):
    """
    Ebers–Moll BJT.

    Parameters
    ----------
    name : str
        Component identifier (e.g. ``'Q1'``).
    nodes : tuple[Node, Node, Node]
        ``(collector, base, emitter)``
    bjt_type : BJTType
        ``BJTType.NPN`` or ``BJTType.PNP``.
    Is : float
        Transport saturation current (A).  Default ``1e-15``.
    BF : float
        Forward current gain β_F.  Default ``100``.
    BR : float
        Reverse current gain β_R.  Default ``1.0``.
    Nf : float
        Forward emission coefficient.  Default ``1.0``.
    Nr : float
        Reverse emission coefficient.  Default ``1.0``.
    Vt : float
        Thermal voltage (V).  Default ``0.02585`` (≈ 300 K).
    Vaf : float | None
        Forward Early voltage (V).  ``None`` disables Early effect.
    """

    _Is: float
    _BF: float
    _BR: float
    _Nf: float
    _Nr: float
    _Vt: float
    _Vaf: float | None
    _type: BJTType
    _polarity: int

    _vbe_prev: float
    _vbc_prev: float
    _ic_prev: float
    _ib_prev: float
    _vbe_nr_prev: float
    _vbc_nr_prev: float
    _Vcrit_be: float
    _Vcrit_bc: float

    _G_MIN: float = 1e-12
    _EXP_MAX: float = 500.0
    _BOLTZMANN_Q: float = 8.617333262e-5  # k/q in eV/K

    def __init__(
        self,
        name: str,
        nodes: tuple[Node, Node, Node],
        bjt_type: BJTType = BJTType.NPN,
        *,
        Is: float = 1e-15,
        BF: float = 100.0,
        BR: float = 1.0,
        Nf: float = 1.0,
        Nr: float = 1.0,
        Vt: float = 0.02585,
        Vaf: float | None = None,
        Tnom: float = 300.15,
        Eg: float = 1.11,
    ):
        if Is <= 0:
            raise ValueError(f"BJT '{name}': Is must be positive, got {Is}")
        if BF <= 0:
            raise ValueError(f"BJT '{name}': BF must be positive, got {BF}")
        if BR <= 0:
            raise ValueError(f"BJT '{name}': BR must be positive, got {BR}")
        if Nf <= 0:
            raise ValueError(f"BJT '{name}': Nf must be positive, got {Nf}")
        if Nr <= 0:
            raise ValueError(f"BJT '{name}': Nr must be positive, got {Nr}")
        if Vt <= 0:
            raise ValueError(f"BJT '{name}': Vt must be positive, got {Vt}")
        if Vaf is not None and Vaf <= 0:
            raise ValueError(f"BJT '{name}': Vaf must be positive, got {Vaf}")
        if len(nodes) != 3:
            raise ValueError(
                f"BJT '{name}': requires exactly 3 nodes "
                f"(collector, base, emitter)"
            )

        super().__init__(name, nodes)
        self._Is = Is
        self._BF = BF
        self._BR = BR
        self._Nf = Nf
        self._Nr = Nr
        self._Vt = Vt
        self._Vaf = Vaf
        self._Tnom = Tnom
        self._Eg = Eg
        self._type = bjt_type
        self._polarity = bjt_type.value

        self._vbe_prev = 0.0
        self._vbc_prev = 0.0
        self._ic_prev = 0.0
        self._ib_prev = 0.0
        self._vbe_nr_prev = 0.0
        self._vbc_nr_prev = 0.0

        nfVt = Nf * Vt
        nrVt = Nr * Vt
        self._Vcrit_be = nfVt * math.log(nfVt / (math.sqrt(2.0) * Is))
        self._Vcrit_bc = nrVt * math.log(nrVt / (math.sqrt(2.0) * Is))

    # ── properties ──────────────────────────────────────────────────
    @property
    def IsNonlinear(self) -> bool:
        return True

    @property
    def Type(self) -> BJTType:
        return self._type

    @property
    def SaturationCurrent(self) -> float:
        return self._Is

    @property
    def ForwardGain(self) -> float:
        return self._BF

    @property
    def ReverseGain(self) -> float:
        return self._BR

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
        """Return ``(Vbe, Vbc)`` with PNP polarity inversion applied."""
        vc = self._node_voltage(x, 0)
        vb = self._node_voltage(x, 1)
        ve = self._node_voltage(x, 2)

        p = self._polarity
        Vbe = p * (vb - ve)
        Vbc = p * (vb - vc)
        return Vbe, Vbc

    def _safe_exp(self, x: float) -> float:
        return math.exp(min(x, self._EXP_MAX))

    def _limit_voltage(self, Vnew: float, Vold: float,
                       Vcrit: float, nVt: float) -> float:
        """SPICE-style PN-junction voltage limiting."""
        if Vnew > Vcrit and abs(Vnew - Vold) > 2.0 * nVt:
            if Vold > 0.0:
                arg = 1.0 + (Vnew - Vold) / nVt
                if arg > 0.0:
                    Vnew = Vold + nVt * math.log(arg)
                else:
                    Vnew = Vcrit
            else:
                Vnew = nVt * math.log(Vnew / nVt) if Vnew > 0 else Vcrit
        if Vnew < -5.0 * Vcrit:
            Vnew = -5.0 * Vcrit
        return Vnew

    def _effective_params(self, T: float) -> tuple[float, float]:
        """Return ``(Is_eff, Vt_eff)`` at temperature *T* (kelvin)."""
        if abs(T - self._Tnom) < 0.01:
            return self._Is, self._Vt
        Vt_eff = self._BOLTZMANN_Q * T
        ratio = T / self._Tnom
        Is_eff = self._Is * (ratio ** 3.0) * math.exp(
            self._Eg * (1.0 / self._Tnom - 1.0 / T) / self._BOLTZMANN_Q
        )
        return Is_eff, Vt_eff

    def _evaluate(self, Vbe: float, Vbc: float,
                  Is: float | None = None,
                  Vt: float | None = None) -> dict:
        """Evaluate all BJT sub-circuit currents and conductances."""
        Is = Is if Is is not None else self._Is
        Vt = Vt if Vt is not None else self._Vt
        BF = self._BF
        BR = self._BR
        nfVt = self._Nf * Vt
        nrVt = self._Nr * Vt

        expf = self._safe_exp(Vbe / nfVt)
        expr = self._safe_exp(Vbc / nrVt)

        If = Is * (expf - 1.0)
        gmf = max((Is / nfVt) * expf, self._G_MIN)

        Ir = Is * (expr - 1.0)
        gmr = max((Is / nrVt) * expr, self._G_MIN)

        I_be = If / BF
        gbe = max(gmf / BF, self._G_MIN)

        I_bc = Ir / BR
        gbc = max(gmr / BR, self._G_MIN)

        # Early effect
        gmf_vbc = 0.0
        if self._Vaf is not None:
            early = max(1.0 + Vbc / self._Vaf, 0.01)
            If = If * early
            gmf_vbc = Is * (expf - 1.0) / self._Vaf

        return {
            "I_be": I_be, "gbe": gbe,
            "I_bc": I_bc, "gbc": gbc,
            "If": If, "gmf": gmf, "gmf_vbc": gmf_vbc,
            "Ir": Ir, "gmr": gmr,
        }

    # ── stamp ───────────────────────────────────────────────────────
    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        # Temperature-adjusted parameters
        Is_eff, Vt_eff = self._effective_params(context.temperature)

        # Operating point
        if context.x_current is not None:
            Vbe0, Vbc0 = self._get_voltages(context.x_current)
        else:
            Vbe0 = self._vbe_prev
            Vbc0 = self._vbc_prev

        # Voltage limiting
        if context.is_nonlinear_iteration:
            Vbe_ref = self._vbe_nr_prev
            Vbc_ref = self._vbc_nr_prev
        else:
            Vbe_ref = self._vbe_prev
            Vbc_ref = self._vbc_prev

        nfVt = self._Nf * Vt_eff
        nrVt = self._Nr * Vt_eff

        Vbe0 = self._limit_voltage(Vbe0, Vbe_ref, self._Vcrit_be, nfVt)
        Vbc0 = self._limit_voltage(Vbc0, Vbc_ref, self._Vcrit_bc, nrVt)

        if context.is_nonlinear_iteration:
            self._vbe_nr_prev = Vbe0
            self._vbc_nr_prev = Vbc0

        ev = self._evaluate(Vbe0, Vbc0, Is=Is_eff, Vt=Vt_eff)

        I_be = ev["I_be"];  gbe = ev["gbe"]
        I_bc = ev["I_bc"];  gbc = ev["gbc"]
        If   = ev["If"];    gmf = ev["gmf"];  gmf_vbc = ev["gmf_vbc"]
        Ir   = ev["Ir"];    gmr = ev["gmr"]

        Ieq_be  = I_be - gbe * Vbe0
        Ieq_bc  = I_bc - gbc * Vbc0
        Ieq_ctf = If   - gmf * Vbe0 - gmf_vbc * Vbc0
        Ieq_ctr = Ir   - gmr * Vbc0

        c  = self.Nodes[0].Index   # collector
        bi = self.Nodes[1].Index   # base
        e  = self.Nodes[2].Index   # emitter
        p  = self._polarity

        # 1. BE junction diode (gbe between B–E)
        if bi is not None:
            A[bi, bi] += gbe
        if e is not None:
            A[e, e] += gbe
        if bi is not None and e is not None:
            A[bi, e] -= gbe
            A[e, bi] -= gbe

        if bi is not None:
            b[bi] -= p * Ieq_be
        if e is not None:
            b[e] += p * Ieq_be

        # 2. BC junction diode (gbc between B–C)
        if bi is not None:
            A[bi, bi] += gbc
        if c is not None:
            A[c, c] += gbc
        if bi is not None and c is not None:
            A[bi, c] -= gbc
            A[c, bi] -= gbc

        if bi is not None:
            b[bi] -= p * Ieq_bc
        if c is not None:
            b[c] += p * Ieq_bc

        # 3. Forward transport VCCS: gmf·Vbe leaving C, entering E
        if c is not None:
            if bi is not None:
                A[c, bi] += gmf
            if e is not None:
                A[c, e] -= gmf
        if e is not None:
            if bi is not None:
                A[e, bi] -= gmf
            if e is not None:
                A[e, e] += gmf

        # Early-effect VCCS term
        if gmf_vbc != 0.0:
            if c is not None:
                if bi is not None:
                    A[c, bi] += gmf_vbc
                if c is not None:
                    A[c, c] -= gmf_vbc
            if e is not None:
                if bi is not None:
                    A[e, bi] -= gmf_vbc
                if c is not None:
                    A[e, c] += gmf_vbc

        if c is not None:
            b[c] -= p * Ieq_ctf
        if e is not None:
            b[e] += p * Ieq_ctf

        # 4. Reverse transport VCCS: gmr·Vbc leaving E, entering C
        if e is not None:
            if bi is not None:
                A[e, bi] += gmr
            if c is not None:
                A[e, c] -= gmr
        if c is not None:
            if bi is not None:
                A[c, bi] -= gmr
            if c is not None:
                A[c, c] += gmr

        if e is not None:
            b[e] -= p * Ieq_ctr
        if c is not None:
            b[c] += p * Ieq_ctr

    # ── state update ────────────────────────────────────────────────
    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        Vbe, Vbc = self._get_voltages(solutionVector)
        ev = self._evaluate(Vbe, Vbc)

        self._vbe_prev = Vbe
        self._vbc_prev = Vbc
        self._vbe_nr_prev = Vbe
        self._vbc_nr_prev = Vbc

        Ic_int = ev["If"] - ev["Ir"] - ev["I_bc"]
        Ib_int = ev["I_be"] + ev["I_bc"]

        self._ic_prev = Ic_int
        self._ib_prev = Ib_int

    # ── query helpers ───────────────────────────────────────────────
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """Return collector current (A)."""
        return self._polarity * self._ic_prev

    def GetBaseCurrent(self, solutionVector: np.ndarray) -> float:
        """Return base current (A)."""
        return self._polarity * self._ib_prev

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return Vce (collector-to-emitter voltage)."""
        vc = self._node_voltage(solutionVector, 0)
        ve = self._node_voltage(solutionVector, 2)
        return vc - ve

    def GetVbe(self, solutionVector: np.ndarray) -> float:
        vb = self._node_voltage(solutionVector, 1)
        ve = self._node_voltage(solutionVector, 2)
        return vb - ve

    def GetVbc(self, solutionVector: np.ndarray) -> float:
        vb = self._node_voltage(solutionVector, 1)
        vc = self._node_voltage(solutionVector, 0)
        return vb - vc


# ── convenience factories ───────────────────────────────────────────
def NPN(name: str, nodes: tuple[Node, Node, Node], *,
        Is: float = 1e-15, BF: float = 100.0, BR: float = 1.0,
        Nf: float = 1.0, Nr: float = 1.0, Vt: float = 0.02585,
        Vaf: float | None = None) -> BJT:
    """Create an NPN bipolar junction transistor."""
    return BJT(name, nodes, BJTType.NPN,
               Is=Is, BF=BF, BR=BR, Nf=Nf, Nr=Nr, Vt=Vt, Vaf=Vaf)


def PNP(name: str, nodes: tuple[Node, Node, Node], *,
        Is: float = 1e-15, BF: float = 100.0, BR: float = 1.0,
        Nf: float = 1.0, Nr: float = 1.0, Vt: float = 0.02585,
        Vaf: float | None = None) -> BJT:
    """Create a PNP bipolar junction transistor."""
    return BJT(name, nodes, BJTType.PNP,
               Is=Is, BF=BF, BR=BR, Nf=Nf, Nr=Nr, Vt=Vt, Vaf=Vaf)
