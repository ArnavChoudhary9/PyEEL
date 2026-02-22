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
    _Vcrit: float
    _current: float
    _v_prev: float
    _v_nr_prev: float

    _EXP_MAX: float = 500.0

    def __init__(self, name: str, nodes: tuple[Node, Node], *,
                 Is: float = 1e-14,
                 n: float = 1.0,
                 Vt: float = 0.02585):
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
        self._current = 0.0
        self._v_prev = 0.0
        self._v_nr_prev = 0.0

        nVt = n * Vt
        self._Vcrit = nVt * math.log(nVt / (math.sqrt(2.0) * Is))

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

    def _evaluate(self, Vd: float) -> tuple[float, float]:
        """Evaluate diode current and conductance.  Returns ``(I_d, G_d)``."""
        nVt = self._n * self._Vt
        e = self._safe_exp(Vd / nVt)

        Id = self._Is * (e - 1.0)
        Gd = (self._Is / nVt) * e
        Gd = max(Gd, self._Is / nVt)

        return Id, Gd

    # ── stamp ───────────────────────────────────────────────────────
    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
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

        Id0, Gd = self._evaluate(Vd0)
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
