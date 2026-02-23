"""
Ideal PN-junction diode using the Shockley equation.

The diode is a **nonlinear** component that requires Newton-Raphson
iteration.  During each NR step the diode linearises around the
current operating-point voltage and stamps an equivalent conductance
in parallel with a correction current source.

Shockley equation::

    I_d = I_s · (exp(V_d / (n · V_t)) - 1)

Convention: current flows from anode (``Nodes[0]``) to cathode
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


class Diode(Component):
    """
    PN-junction diode (Shockley model).

    Parameters
    ----------
    name : str
        Component identifier (e.g. ``'D1'``).
    nodes : tuple[Node, Node]
        ``(anode, cathode)``  — current flows anode → cathode.
    Is : float
        Saturation current (A).  Default ``1e-14``.
    n : float
        Emission coefficient (ideality factor).  Default ``1.0``.
    Vt : float
        Thermal voltage (V).  Default ``0.02585`` (≈ 300 K).
    """

    _Is: float
    _n: float
    _Vt: float
    _Tnom: float       # nominal temperature (K)
    _Eg: float         # band-gap energy (eV)
    _Vcrit: float
    _current: float
    _v_prev: float
    _v_nr_prev: float

    _EXP_MAX: float = 500.0
    _BOLTZMANN_Q: float = 8.617333262e-5  # k/q in eV/K

    def __init__(self, name: str, nodes: tuple[Node, Node], *,
                 Is: float = 1e-14,
                 n: float = 1.0,
                 Vt: float = 0.02585,
                 Tnom: float = 300.15,
                 Eg: float = 1.11):
        if Is <= 0:
            raise ValueError(f"Diode '{name}': Is must be positive, got {Is}")
        if n <= 0:
            raise ValueError(f"Diode '{name}': n must be positive, got {n}")
        if Vt <= 0:
            raise ValueError(f"Diode '{name}': Vt must be positive, got {Vt}")

        super().__init__(name, nodes)
        self._Is = Is
        self._n = n
        self._Vt = Vt
        self._Tnom = Tnom
        self._Eg = Eg
        self._current = 0.0
        self._v_prev = 0.0
        self._v_nr_prev = 0.0

        nVt = n * Vt
        self._Vcrit = nVt * math.log(nVt / (math.sqrt(2.0) * Is))

    # ── temperature helpers ─────────────────────────────────────────
    def _effective_params(self, T: float) -> tuple[float, float]:
        """
        Return ``(Is_eff, Vt_eff)`` at temperature *T* (kelvin).

        SPICE temperature model:
            Vt = k·T/q
            Is(T) = Is(Tnom) · (T/Tnom)^(3/n) · exp((Eg/n)·(1/Tnom - 1/T) / (k/q))
        """
        if abs(T - self._Tnom) < 0.01:
            return self._Is, self._Vt
        Vt_eff = self._BOLTZMANN_Q * T
        ratio = T / self._Tnom
        Is_eff = self._Is * (ratio ** (3.0 / self._n)) * self._safe_exp(
            (self._Eg / self._n) * (1.0 / self._Tnom - 1.0 / T) / self._BOLTZMANN_Q
        )
        return Is_eff, Vt_eff

    # ── properties ──────────────────────────────────────────────────
    @property
    def IsNonlinear(self) -> bool:
        return True

    @property
    def SaturationCurrent(self) -> float:
        return self._Is

    @property
    def EmissionCoefficient(self) -> float:
        return self._n

    @property
    def ThermalVoltage(self) -> float:
        return self._Vt

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
        """SPICE-style PN-junction voltage limiting."""
        nVt = self._n * self._Vt
        Vcrit = self._Vcrit

        if Vd_new > Vcrit and abs(Vd_new - Vd_old) > 2.0 * nVt:
            if Vd_old > 0.0:
                arg = 1.0 + (Vd_new - Vd_old) / nVt
                if arg > 0.0:
                    Vd_new = Vd_old + nVt * math.log(arg)
                else:
                    Vd_new = Vcrit
            else:
                Vd_new = nVt * math.log(Vd_new / nVt)

        if Vd_new < -5.0 * self._Vcrit:
            Vd_new = -5.0 * self._Vcrit

        return Vd_new

    def _safe_exp(self, x: float) -> float:
        return math.exp(min(x, self._EXP_MAX))

    def _evaluate(self, Vd: float, Is: float | None = None,
                  Vt: float | None = None) -> tuple[float, float]:
        """Evaluate diode current and conductance.  Returns ``(I_d, G_d)``."""
        _Is = Is if Is is not None else self._Is
        _Vt = Vt if Vt is not None else self._Vt
        nVt = self._n * _Vt
        e = self._safe_exp(Vd / nVt)

        Id = _Is * (e - 1.0)
        Gd = (_Is / nVt) * e
        Gd = max(Gd, _Is / nVt)

        return Id, Gd

    # ── stamp ───────────────────────────────────────────────────────
    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        # Temperature-adjusted parameters
        Is_eff, Vt_eff = self._effective_params(context.temperature)

        # Determine operating-point voltage
        if context.x_current is not None:
            Vd0 = self._get_vd(context.x_current)
        else:
            Vd0 = self._v_prev

        Vd_ref = (self._v_nr_prev if context.is_nonlinear_iteration
                  else self._v_prev)
        Vd0 = self._limit_voltage(Vd0, Vd_ref)

        if context.is_nonlinear_iteration:
            self._v_nr_prev = Vd0

        Id0, Gd = self._evaluate(Vd0, Is=Is_eff, Vt=Vt_eff)
        Ieq = Id0 - Gd * Vd0

        n1 = self.Nodes[0].Index   # anode
        n2 = self.Nodes[1].Index   # cathode

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
