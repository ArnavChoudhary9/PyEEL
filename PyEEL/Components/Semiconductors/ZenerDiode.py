"""
Zener diode model.

Extends the standard PN-junction :class:`Diode` with a reverse
breakdown region.  In forward bias the device behaves identically to
a regular diode.  In reverse bias, once ``|V_d|`` exceeds the Zener
breakdown voltage ``V_z``, an exponentially increasing reverse
current flows.

Total diode current::

    I_d = I_fwd - I_rev

Convention: same as :class:`Diode` — anode (``Nodes[0]``) to cathode
(``Nodes[1]``).
"""

from __future__ import annotations

import math
import numpy as np

from ...Core.Node import Node
from ...Core.NodeManager import NodeManager
from ...Core.SimulationContext import SimulationContext, SimulationMode
from ..Component import Component
from ..stamp_helpers import stamp_conductance, stamp_current_source, get_voltage_across


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
    _Vcrit_fwd: float
    _Vcrit_rev: float
    _current: float
    _v_prev: float
    _v_nr_prev: float

    _EXP_MAX: float = 500.0
    _BOLTZMANN_Q: float = 8.617333262e-5

    def __init__(self, name: str, nodes: tuple[Node, Node], *,
                 Vz: float = 5.1,
                 Is: float = 1e-14,
                 n: float = 1.0,
                 Ibv: float = 1e-3,
                 n_bv: float = 1.0,
                 Vt: float = 0.02585,
                 Tnom: float = 300.15,
                 Eg: float = 1.11):
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
        self._Tnom = Tnom
        self._Eg = Eg

        nVt = n * Vt
        self._Vcrit_fwd = nVt * math.log(nVt / (math.sqrt(2.0) * Is))
        n_bv_Vt = n_bv * Vt
        self._Vcrit_rev = n_bv_Vt * math.log(n_bv_Vt / (math.sqrt(2.0) * Ibv))

    # ── properties ──────────────────────────────────────────────────
    @property
    def IsNonlinear(self) -> bool:
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

    # ── temperature ─────────────────────────────────────────────────
    def _effective_params(self, T: float) -> tuple[float, float]:
        """Return ``(Is_eff, Vt_eff)`` at temperature *T* (kelvin)."""
        if abs(T - self._Tnom) < 0.01:
            return self._Is, self._Vt
        Vt_eff = self._BOLTZMANN_Q * T
        ratio = T / self._Tnom
        Is_eff = self._Is * (ratio ** (3.0 / self._n)) * self._safe_exp(
            (self._Eg / self._n) * (1.0 / self._Tnom - 1.0 / T) / self._BOLTZMANN_Q
        )
        return Is_eff, Vt_eff

    # ── MNA interface ───────────────────────────────────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        pass

    # ── helpers ─────────────────────────────────────────────────────
    def _get_vd(self, solutionVector: np.ndarray | None) -> float:
        if solutionVector is None:
            return 0.0
        return get_voltage_across(solutionVector,
                                  self.Nodes[0].Index, self.Nodes[1].Index)

    def _limit_voltage(self, Vd_new: float, Vd_old: float) -> float:
        """SPICE-style voltage limiting for both forward and reverse bias."""
        nVt = self._n * self._Vt

        # Forward limiting
        if Vd_new > self._Vcrit_fwd and abs(Vd_new - Vd_old) > 2.0 * nVt:
            if Vd_old > 0.0:
                arg = 1.0 + (Vd_new - Vd_old) / nVt
                if arg > 0.0:
                    Vd_new = Vd_old + nVt * math.log(arg)
                else:
                    Vd_new = self._Vcrit_fwd
            else:
                Vd_new = (nVt * math.log(Vd_new / nVt)
                          if Vd_new > 0 else self._Vcrit_fwd)

        # Reverse limiting
        n_bv_Vt = self._n_bv * self._Vt
        Vz = self._Vz
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
                rev_limited = (n_bv_Vt * math.log(rev_excess / n_bv_Vt)
                               if rev_excess > 0 else rev_crit)
            Vd_new = -(rev_limited + Vz)

        return Vd_new

    def _safe_exp(self, x: float) -> float:
        return math.exp(min(x, self._EXP_MAX))

    def _evaluate(self, Vd: float, Is: float | None = None,
                  Vt: float | None = None) -> tuple[float, float]:
        """Evaluate total Zener current and conductance. Returns ``(I, G)``."""
        _Is = Is if Is is not None else self._Is
        _Vt = Vt if Vt is not None else self._Vt
        nVt = self._n * _Vt
        n_bv_Vt = self._n_bv * _Vt

        # Forward (Shockley)
        ef = self._safe_exp(Vd / nVt)
        I_fwd = _Is * (ef - 1.0)
        G_fwd = (_Is / nVt) * ef
        G_fwd = max(G_fwd, _Is / nVt)

        # Reverse breakdown
        rev_arg = -(Vd + self._Vz) / n_bv_Vt
        er = self._safe_exp(rev_arg)
        I_rev = self._Ibv * er
        G_rev = (self._Ibv / n_bv_Vt) * er

        I_total = I_fwd - I_rev
        G_total = G_fwd + G_rev
        G_total = max(G_total, _Is / nVt)

        return I_total, G_total

    # ── stamp ───────────────────────────────────────────────────────
    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        if context.x_current is not None:
            Vd0 = self._get_vd(context.x_current)
        else:
            Vd0 = self._v_prev

        Vd_ref = (self._v_nr_prev if context.is_nonlinear_iteration
                  else self._v_prev)
        Vd0 = self._limit_voltage(Vd0, Vd_ref)

        if context.is_nonlinear_iteration:
            self._v_nr_prev = Vd0

        Is_eff, Vt_eff = self._effective_params(context.temperature)
        Id0, Gd = self._evaluate(Vd0, Is=Is_eff, Vt=Vt_eff)
        Ieq = Id0 - Gd * Vd0

        n1 = self.Nodes[0].Index
        n2 = self.Nodes[1].Index

        stamp_conductance(A, n1, n2, Gd)
        stamp_current_source(b, n1, n2, Ieq)

    # ── state update ────────────────────────────────────────────────
    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        Vd = self._get_vd(solutionVector)
        Id, _ = self._evaluate(Vd)
        self._v_prev = Vd
        self._v_nr_prev = Vd
        self._current = Id

    # ── query helpers ───────────────────────────────────────────────
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        return self._current

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        return self._get_vd(solutionVector)
