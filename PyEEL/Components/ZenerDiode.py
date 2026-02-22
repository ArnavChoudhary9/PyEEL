"""
Zener diode model.

Extends the standard PN-junction :class:`Diode` with a reverse
breakdown region.  In forward bias the device behaves identically to
a regular diode.  In reverse bias, once ``|V_d|`` exceeds the Zener
breakdown voltage ``V_z``, an exponentially increasing reverse
current flows.

Total diode current
-------------------
::

    I_d = I_fwd - I_rev

where

**Forward** (standard Shockley)::

    I_fwd = I_s · [exp(V_d / (n · V_t)) - 1]

**Reverse / breakdown**::

    I_rev = I_bv · exp[-(V_d + V_z) / (n_bv · V_t)]

``I_rev`` is negligible for ``V_d > -V_z`` and grows exponentially
once the reverse voltage exceeds ``V_z``.

Parameters
----------
V_z  — Zener (breakdown) voltage (V), positive number.  Default ``5.1``.
I_bv — Reverse-breakdown knee current (A).  Default ``1e-3``
        (sets the sharpness of the knee).
n_bv — Reverse-breakdown emission coefficient.  Default ``1.0``.

Convention
----------
Same as :class:`Diode`: current flows from anode (``Nodes[0]``) to
cathode (``Nodes[1]``).  ``V_d = V(anode) - V(cathode)``.

When used as a voltage regulator the cathode is connected to the
more positive rail (reverse biased); the regulated voltage across
the Zener is approximately ``V_z``.
"""

from __future__ import annotations

import math
import numpy as np

from ..Node import Node
from ..NodeManager import NodeManager
from ..SimulationContext import SimulationContext, SimulationMode
from .Component import Component


class ZenerDiode(Component):
    """
    Zener (breakdown) diode.

    Parameters
    ----------
    name : str
        Component identifier (e.g. ``'DZ1'``).
    nodes : tuple[Node, Node]
        ``(anode, cathode)``  — current flows anode → cathode.
    Vz : float
        Zener breakdown voltage (V), positive.  Default ``5.1``.
    Is : float
        Forward saturation current (A).  Default ``1e-14``.
    n : float
        Forward emission coefficient.  Default ``1.0``.
    Ibv : float
        Reverse breakdown knee current (A).  Default ``1e-3``.
    n_bv : float
        Reverse breakdown emission coefficient.  Default ``1.0``.
    Vt : float
        Thermal voltage (V).  Default ``0.02585`` (≈ 300 K).
    """

    _Is: float
    _n: float
    _Vt: float
    _Vz: float
    _Ibv: float
    _n_bv: float
    _Vcrit_fwd: float      # forward critical voltage for limiting
    _Vcrit_rev: float      # reverse critical voltage for limiting
    _current: float         # last computed total current
    _v_prev: float          # converged voltage from previous time-step
    _v_nr_prev: float       # NR-tracked voltage

    _EXP_MAX: float = 500.0

    def __init__(self, name: str, nodes: tuple[Node, Node], *,
                 Vz: float = 5.1,
                 Is: float = 1e-14,
                 n: float = 1.0,
                 Ibv: float = 1e-3,
                 n_bv: float = 1.0,
                 Vt: float = 0.02585):
        if Vz <= 0:
            raise ValueError(f"ZenerDiode '{name}': Vz must be positive, got {Vz}")
        if Is <= 0:
            raise ValueError(f"ZenerDiode '{name}': Is must be positive, got {Is}")
        if n <= 0:
            raise ValueError(f"ZenerDiode '{name}': n must be positive, got {n}")
        if Ibv <= 0:
            raise ValueError(f"ZenerDiode '{name}': Ibv must be positive, got {Ibv}")
        if n_bv <= 0:
            raise ValueError(f"ZenerDiode '{name}': n_bv must be positive, got {n_bv}")
        if Vt <= 0:
            raise ValueError(f"ZenerDiode '{name}': Vt must be positive, got {Vt}")
        if len(nodes) != 2:
            raise ValueError(
                f"ZenerDiode '{name}': requires exactly 2 nodes (anode, cathode)"
            )

        super().__init__(name, nodes)
        self._Is = Is
        self._n = n
        self._Vt = Vt
        self._Vz = Vz
        self._Ibv = Ibv
        self._n_bv = n_bv
        self._current = 0.0
        self._v_prev = 0.0
        self._v_nr_prev = 0.0

        # Critical voltages for SPICE-style limiting
        nVt = n * Vt
        self._Vcrit_fwd = nVt * math.log(nVt / (math.sqrt(2.0) * Is))
        n_bv_Vt = n_bv * Vt
        self._Vcrit_rev = n_bv_Vt * math.log(n_bv_Vt / (math.sqrt(2.0) * Ibv))

    # ── properties ──────────────────────────────────────────────────
    @property
    def IsNonlinear(self) -> bool:
        """This component requires Newton-Raphson iteration."""
        return True

    @property
    def ZenerVoltage(self) -> float:
        return self._Vz

    @property
    def SaturationCurrent(self) -> float:
        return self._Is

    @property
    def EmissionCoefficient(self) -> float:
        return self._n

    @property
    def ThermalVoltage(self) -> float:
        return self._Vt

    @property
    def BreakdownCurrent(self) -> float:
        return self._Ibv

    # ── MNA interface ───────────────────────────────────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        """Zener diodes introduce no auxiliary unknowns."""
        pass

    # ── helpers ─────────────────────────────────────────────────────
    def _get_vd(self, solutionVector: np.ndarray | None) -> float:
        """Read ``V(anode) - V(cathode)`` from a solution vector."""
        if solutionVector is None:
            return 0.0
        n1 = self.Nodes[0].Index
        n2 = self.Nodes[1].Index
        v1 = float(solutionVector[n1]) if n1 is not None else 0.0
        v2 = float(solutionVector[n2]) if n2 is not None else 0.0
        return v1 - v2

    def _limit_voltage(self, Vd_new: float, Vd_old: float) -> float:
        """
        SPICE-style voltage limiting for both forward and reverse bias.

        Forward limiting prevents ``exp()`` overflow in the Shockley
        term.  Reverse limiting prevents overflow in the breakdown
        exponential.
        """
        nVt = self._n * self._Vt

        # ── forward limiting ────────────────────────────────────────
        if Vd_new > self._Vcrit_fwd and abs(Vd_new - Vd_old) > 2.0 * nVt:
            if Vd_old > 0.0:
                arg = 1.0 + (Vd_new - Vd_old) / nVt
                if arg > 0.0:
                    Vd_new = Vd_old + nVt * math.log(arg)
                else:
                    Vd_new = self._Vcrit_fwd
            else:
                Vd_new = nVt * math.log(Vd_new / nVt) if Vd_new > 0 else self._Vcrit_fwd

        # ── reverse limiting ────────────────────────────────────────
        n_bv_Vt = self._n_bv * self._Vt
        Vz = self._Vz
        # The breakdown exponential argument is -(Vd + Vz) / n_bv_Vt.
        # Vd is negative in reverse bias, so -(Vd+Vz) > 0 when |Vd| > Vz.
        # Limit when the reverse voltage is far beyond Vz.
        rev_excess = -(Vd_new + Vz)
        rev_crit = self._Vcrit_rev
        if rev_excess > rev_crit and abs(Vd_new - Vd_old) > 2.0 * n_bv_Vt:
            rev_old = -(Vd_old + Vz)
            if rev_old > 0.0:
                arg = 1.0 + (rev_excess - rev_old) / n_bv_Vt
                if arg > 0.0:
                    rev_limited = rev_old + n_bv_Vt * math.log(arg)
                else:
                    rev_limited = rev_crit
            else:
                rev_limited = n_bv_Vt * math.log(rev_excess / n_bv_Vt) if rev_excess > 0 else rev_crit
            Vd_new = -(rev_limited + Vz)

        return Vd_new

    def _safe_exp(self, x: float) -> float:
        """``exp(x)`` clamped to prevent overflow."""
        return math.exp(min(x, self._EXP_MAX))

    def _evaluate(self, Vd: float) -> tuple[float, float]:
        """
        Evaluate total Zener diode current and conductance.

        Returns ``(I_total, G_total)`` where the total current is the
        sum of the forward Shockley current and the reverse breakdown
        current::

            I_total = I_fwd - I_rev
            G_total = G_fwd + G_rev

        The minus sign on ``I_rev`` accounts for the reverse direction.
        """
        nVt = self._n * self._Vt
        n_bv_Vt = self._n_bv * self._Vt

        # ── forward current (Shockley) ──────────────────────────────
        ef = self._safe_exp(Vd / nVt)
        I_fwd = self._Is * (ef - 1.0)
        G_fwd = (self._Is / nVt) * ef
        G_fwd = max(G_fwd, self._Is / nVt)

        # ── reverse breakdown current ───────────────────────────────
        # I_rev = Ibv · exp(-(Vd + Vz) / (n_bv · Vt))
        # This is large when Vd << -Vz (reverse beyond breakdown).
        rev_arg = -(Vd + self._Vz) / n_bv_Vt
        er = self._safe_exp(rev_arg)
        I_rev = self._Ibv * er
        # G_rev = dI_rev / dVd = -Ibv / (n_bv·Vt) · exp(-(Vd+Vz)/(n_bv·Vt))
        # Since I_rev is subtracted from I_total, the contribution to
        # G_total is +|dI_rev/dVd| = Ibv/(n_bv·Vt) · exp(...)
        G_rev = (self._Ibv / n_bv_Vt) * er

        # ── total ───────────────────────────────────────────────────
        I_total = I_fwd - I_rev
        G_total = G_fwd + G_rev

        # Floor conductance
        G_total = max(G_total, self._Is / nVt)

        return I_total, G_total

    # ── stamp ───────────────────────────────────────────────────────
    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        """
        Stamp the Newton-Raphson companion model into the MNA system.

        Companion model::

            I_d ≈ G_d · V_d + I_eq
            where  I_eq = I_d(V_d0) - G_d · V_d0

        ``G_d`` is stamped identically to a resistor, and ``I_eq`` is
        stamped as a current source entering the anode / leaving the
        cathode.
        """
        # --- determine operating-point voltage -----------------------
        if context.x_current is not None:
            Vd0 = self._get_vd(context.x_current)
        else:
            Vd0 = self._v_prev

        # Voltage limiting
        if context.is_nonlinear_iteration:
            Vd_ref = self._v_nr_prev
        else:
            Vd_ref = self._v_prev

        Vd0 = self._limit_voltage(Vd0, Vd_ref)

        if context.is_nonlinear_iteration:
            self._v_nr_prev = Vd0

        Id0, Gd = self._evaluate(Vd0)

        # Equivalent current source
        Ieq = Id0 - Gd * Vd0

        # --- stamp conductance Gd (resistor pattern) ----------------
        n1 = self.Nodes[0].Index   # anode
        n2 = self.Nodes[1].Index   # cathode

        if n1 is not None and n2 is not None:
            A[n1, n1] += Gd
            A[n1, n2] -= Gd
            A[n2, n1] -= Gd
            A[n2, n2] += Gd
        elif n1 is not None:
            A[n1, n1] += Gd
        elif n2 is not None:
            A[n2, n2] += Gd

        # --- stamp current source Ieq (positive = into anode) -------
        if n1 is not None:
            b[n1] -= Ieq
        if n2 is not None:
            b[n2] += Ieq

    # ── state update ────────────────────────────────────────────────
    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        """Store the converged voltage for the next NR sweep."""
        Vd = self._get_vd(solutionVector)
        Id, _ = self._evaluate(Vd)
        self._v_prev = Vd
        self._v_nr_prev = Vd
        self._current = Id

    # ── query helpers ───────────────────────────────────────────────
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """Return total diode current (anode → cathode, A)."""
        return self._current

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return voltage across the diode ``V(anode) - V(cathode)``."""
        return self._get_vd(solutionVector)
