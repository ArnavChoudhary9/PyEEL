"""
Ebers–Moll BJT model (NPN / PNP).

Implements bipolar junction transistors as nonlinear three-terminal
components.  During Newton-Raphson iteration the device is linearised
around the current operating point and stamped as companion
conductances plus current sources.

Ebers–Moll transport model
--------------------------
The BJT is decomposed into three sub-circuits:

1. **BE junction diode** (base → emitter)::

       I_be = (I_s / β_F) · [exp(V_be / (N_f · V_t)) - 1]

2. **BC junction diode** (base → collector)::

       I_bc = (I_s / β_R) · [exp(V_bc / (N_r · V_t)) - 1]

3. **Forward transport current** (collector ← emitter)::

       I_f = I_s · [exp(V_be / (N_f · V_t)) - 1]

4. **Reverse transport current** (collector → emitter)::

       I_r = I_s · [exp(V_bc / (N_r · V_t)) - 1]

Terminal currents (NPN)
-----------------------
::

    I_c = I_f  - I_r  - I_bc      (into collector)
    I_b = I_be + I_bc              (into base)
    I_e = -(I_c + I_b)            (out of emitter)

For **PNP** all voltage polarities are reversed internally so the
same equations apply (handled by the ``_polarity`` factor).

Terminals
---------
``Nodes = (collector, base, emitter)``

Companion-model stamping
------------------------
Each sub-circuit is linearised independently.  The junction diodes
are stamped like the :class:`Diode` component (conductance + current
source).  The transport sources are stamped as voltage-controlled
current sources (VCCS) plus constant current sources.
"""

from __future__ import annotations

import math
from enum import Enum
import numpy as np

from ..Node import Node
from ..NodeManager import NodeManager
from ..SimulationContext import SimulationContext, SimulationMode
from .Component import Component


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
        Forward Early voltage (V) for output-resistance modelling.
        ``None`` disables Early effect (default).
    """

    _Is: float
    _BF: float
    _BR: float
    _Nf: float
    _Nr: float
    _Vt: float
    _Vaf: float | None
    _type: BJTType
    _polarity: int          # +1 for NPN, -1 for PNP

    _vbe_prev: float
    _vbc_prev: float
    _ic_prev: float
    _ib_prev: float

    # NR tracking for voltage limiting
    _vbe_nr_prev: float
    _vbc_nr_prev: float

    # Critical voltages (SPICE-style limiting)
    _Vcrit_be: float
    _Vcrit_bc: float

    # Small conductance floor
    _G_MIN: float = 1e-12
    # Maximum exponent argument
    _EXP_MAX: float = 500.0

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
        self._type = bjt_type
        self._polarity = bjt_type.value   # +1 NPN, -1 PNP

        self._vbe_prev = 0.0
        self._vbc_prev = 0.0
        self._ic_prev = 0.0
        self._ib_prev = 0.0
        self._vbe_nr_prev = 0.0
        self._vbc_nr_prev = 0.0

        # Critical voltages for SPICE-style limiting
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
        """BJTs introduce no auxiliary unknowns."""
        pass

    # ── helpers ─────────────────────────────────────────────────────
    def _node_voltage(self, solutionVector: np.ndarray | None, idx: int) -> float:
        """Read a node voltage, returning 0 for ground."""
        if solutionVector is None:
            return 0.0
        node = self.Nodes[idx]
        return float(solutionVector[node.Index]) if node.Index is not None else 0.0

    def _get_voltages(self, x: np.ndarray | None) -> tuple[float, float]:
        """
        Return ``(Vbe, Vbc)`` with PNP polarity inversion applied.

        For NPN: Vbe = V(base) - V(emitter), Vbc = V(base) - V(collector)
        For PNP: signs are flipped so internal equations stay identical.
        """
        vc = self._node_voltage(x, 0)
        vb = self._node_voltage(x, 1)
        ve = self._node_voltage(x, 2)

        p = self._polarity
        Vbe = p * (vb - ve)
        Vbc = p * (vb - vc)
        return Vbe, Vbc

    def _safe_exp(self, x: float) -> float:
        """``exp(x)`` clamped to prevent overflow."""
        return math.exp(min(x, self._EXP_MAX))

    def _limit_voltage(self, Vnew: float, Vold: float,
                       Vcrit: float, nVt: float) -> float:
        """
        SPICE-style PN-junction voltage limiting.

        Prevents the Newton step from proposing excessively large
        forward-bias voltages that would cause ``exp()`` overflow.
        """
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

    def _evaluate(self, Vbe: float, Vbc: float) -> dict:
        """
        Evaluate all BJT sub-circuit currents and conductances.

        Returns a dict with keys:

        - ``I_be``, ``gbe``   — BE diode current & conductance
        - ``I_bc``, ``gbc``   — BC diode current & conductance
        - ``If``, ``gmf``     — forward transport current & transconductance
        - ``Ir``, ``gmr``     — reverse transport current & transconductance
        """
        Is = self._Is
        BF = self._BF
        BR = self._BR
        nfVt = self._Nf * self._Vt
        nrVt = self._Nr * self._Vt

        # Forward junction: exp(Vbe / (Nf·Vt))
        expf = self._safe_exp(Vbe / nfVt)
        # Reverse junction: exp(Vbc / (Nr·Vt))
        expr = self._safe_exp(Vbc / nrVt)

        # Forward transport current
        If = Is * (expf - 1.0)
        gmf = (Is / nfVt) * expf
        gmf = max(gmf, self._G_MIN)

        # Reverse transport current
        Ir = Is * (expr - 1.0)
        gmr = (Is / nrVt) * expr
        gmr = max(gmr, self._G_MIN)

        # BE junction diode current (= If / BF)
        I_be = If / BF
        gbe = gmf / BF
        gbe = max(gbe, self._G_MIN)

        # BC junction diode current (= Ir / BR)
        I_bc = Ir / BR
        gbc = gmr / BR
        gbc = max(gbc, self._G_MIN)

        # Early effect (output resistance)
        if self._Vaf is not None:
            # Forward Early voltage modifies forward transport current
            # I_f_early = I_f * (1 + Vbc / Vaf)  — note Vbc is negative
            # in forward-active, so this reduces If slightly; the main
            # effect is an output conductance go = If / Vaf.
            early = 1.0 + Vbc / self._Vaf
            if early < 0.01:
                early = 0.01  # clamp to prevent negative currents
            If = If * early
            # Additional output conductance ∂If/∂Vbc = Is*(expf-1)/Vaf
            gmf_vbc = Is * (expf - 1.0) / self._Vaf
        else:
            gmf_vbc = 0.0

        return {
            "I_be": I_be, "gbe": gbe,
            "I_bc": I_bc, "gbc": gbc,
            "If": If, "gmf": gmf, "gmf_vbc": gmf_vbc,
            "Ir": Ir, "gmr": gmr,
        }

    # ── stamp ───────────────────────────────────────────────────────
    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        """
        Stamp the Newton-Raphson companion model into the MNA system.

        The BJT is decomposed into:

        1. BE junction diode  — conductance ``gbe`` between B–E
           plus current source ``Ieq_be`` (B → E).
        2. BC junction diode  — conductance ``gbc`` between B–C
           plus current source ``Ieq_bc`` (B → C).
        3. Forward transport VCCS — ``gmf · Vbe`` current leaving C,
           entering E, plus current source ``Ieq_ctf``.
        4. Reverse transport VCCS — ``gmr · Vbc`` current leaving E,
           entering C, plus current source ``Ieq_ctr``.
        """
        # --- operating point -----------------------------------------
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

        nfVt = self._Nf * self._Vt
        nrVt = self._Nr * self._Vt

        Vbe0 = self._limit_voltage(Vbe0, Vbe_ref, self._Vcrit_be, nfVt)
        Vbc0 = self._limit_voltage(Vbc0, Vbc_ref, self._Vcrit_bc, nrVt)

        if context.is_nonlinear_iteration:
            self._vbe_nr_prev = Vbe0
            self._vbc_nr_prev = Vbc0

        ev = self._evaluate(Vbe0, Vbc0)

        I_be = ev["I_be"];  gbe = ev["gbe"]
        I_bc = ev["I_bc"];  gbc = ev["gbc"]
        If   = ev["If"];    gmf = ev["gmf"];  gmf_vbc = ev["gmf_vbc"]
        Ir   = ev["Ir"];    gmr = ev["gmr"]

        # Equivalent current sources (linearised remainder)
        Ieq_be  = I_be - gbe * Vbe0               # BE diode
        Ieq_bc  = I_bc - gbc * Vbc0               # BC diode
        Ieq_ctf = If   - gmf * Vbe0 - gmf_vbc * Vbc0   # fwd transport
        Ieq_ctr = Ir   - gmr * Vbc0               # rev transport

        # Node indices (None = ground)
        c = self.Nodes[0].Index   # collector
        bi = self.Nodes[1].Index  # base  (avoid shadowing builtin `b`)
        e = self.Nodes[2].Index   # emitter

        p = self._polarity  # +1 NPN, -1 PNP

        # ============================================================
        # 1. BE junction diode (gbe, Ieq_be) — current B → E
        #    Conductance gbe between B and E
        # ============================================================
        if bi is not None:
            A[bi, bi] += gbe
        if e is not None:
            A[e, e] += gbe
        if bi is not None and e is not None:
            A[bi, e] -= gbe
            A[e, bi] -= gbe

        # Current source Ieq_be: leaves B, enters E
        if bi is not None:
            b[bi] -= p * Ieq_be
        if e is not None:
            b[e] += p * Ieq_be

        # ============================================================
        # 2. BC junction diode (gbc, Ieq_bc) — current B → C
        #    Conductance gbc between B and C
        # ============================================================
        if bi is not None:
            A[bi, bi] += gbc
        if c is not None:
            A[c, c] += gbc
        if bi is not None and c is not None:
            A[bi, c] -= gbc
            A[c, bi] -= gbc

        # Current source Ieq_bc: leaves B, enters C
        if bi is not None:
            b[bi] -= p * Ieq_bc
        if c is not None:
            b[c] += p * Ieq_bc

        # ============================================================
        # 3. Forward transport VCCS: gmf·Vbe leaving C, entering E
        #    I_ctf = gmf·(Vb - Ve) + Ieq_ctf  (current leaves C node)
        #    p² = 1 cancels for conductance stamps.
        # ============================================================
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

        # Early-effect VCCS term: gmf_vbc·(Vb - Vc) from C to E
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

        # Current source Ieq_ctf: leaves C, enters E
        if c is not None:
            b[c] -= p * Ieq_ctf
        if e is not None:
            b[e] += p * Ieq_ctf

        # ============================================================
        # 4. Reverse transport VCCS: gmr·Vbc leaving E, entering C
        #    I_ctr = gmr·(Vb - Vc) + Ieq_ctr  (current leaves E node)
        # ============================================================
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

        # Current source Ieq_ctr: leaves E, enters C
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

        # Terminal currents (internal frame)
        Ic_int = ev["If"] - ev["Ir"] - ev["I_bc"]
        Ib_int = ev["I_be"] + ev["I_bc"]

        self._ic_prev = Ic_int
        self._ib_prev = Ib_int

    # ── query helpers ───────────────────────────────────────────────
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """
        Return collector current (A).

        Positive = current entering collector terminal for NPN.
        """
        return self._polarity * self._ic_prev

    def GetBaseCurrent(self, solutionVector: np.ndarray) -> float:
        """Return base current (A). Positive = into base for NPN."""
        return self._polarity * self._ib_prev

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return Vce (collector-to-emitter voltage)."""
        vc = self._node_voltage(solutionVector, 0)
        ve = self._node_voltage(solutionVector, 2)
        return vc - ve

    def GetVbe(self, solutionVector: np.ndarray) -> float:
        """Return Vbe (base-to-emitter voltage)."""
        vb = self._node_voltage(solutionVector, 1)
        ve = self._node_voltage(solutionVector, 2)
        return vb - ve

    def GetVbc(self, solutionVector: np.ndarray) -> float:
        """Return Vbc (base-to-collector voltage)."""
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
