"""
Ideal PN-junction diode using the Shockley equation.

The diode is a **nonlinear** component that requires Newton-Raphson
iteration.  During each NR step the diode linearises around the
current operating-point voltage ``V_d0`` (read from
``context.x_current``) and stamps an equivalent conductance ``G_d``
in parallel with a correction current source ``I_eq``.

Shockley equation
-----------------
    I_d = I_s · (exp(V_d / (n · V_t)) - 1)

where
    I_s — saturation current (A), default 1 x 10⁻¹⁴ A
    n   — emission coefficient, default 1
    V_t — thermal voltage (kT/q ≈ 25.85 mV at 300 K)

Convention
----------
Current flows from anode (``Nodes[0]``) to cathode (``Nodes[1]``).
``V_d = V(anode) - V(cathode)``.

Voltage limiting
----------------
A SPICE-style logarithmic clamp is applied before evaluating the
exponential to prevent numerical overflow during early NR iterations::

    V_crit = n · V_t · ln(n · V_t / (√2 · I_s))

If the proposed voltage exceeds ``V_crit``, it is compressed via::

    V_d ← V_old + n·V_t · ln(max(1, (V_d - V_old) / (n·V_t) + 1))
"""

from __future__ import annotations

import math
import numpy as np

from ..Node import Node
from ..NodeManager import NodeManager
from ..SimulationContext import SimulationContext, SimulationMode
from .Component import Component


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
    _Vcrit: float          # pre-computed critical voltage for limiting
    _current: float         # last computed diode current (for GetCurrent)
    _v_prev: float          # converged voltage from previous time-step
    _v_nr_prev: float       # operating-point voltage from previous NR iteration

    # ── Maximum exponent argument to prevent overflow ───────────────
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

        # Critical voltage for SPICE-style limiting
        nVt = n * Vt
        self._Vcrit = nVt * math.log(nVt / (math.sqrt(2.0) * Is))

    # ── properties ──────────────────────────────────────────────────
    @property
    def IsNonlinear(self) -> bool:  # noqa: N802  (matches base-class style)
        """This component requires Newton-Raphson iteration."""
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
        """Diodes introduce no auxiliary unknowns."""
        pass

    # ── helpers ─────────────────────────────────────────────────────
    def _get_vd(self, solutionVector: np.ndarray | None) -> float:
        """Read V(anode) − V(cathode) from a solution vector."""
        if solutionVector is None:
            return 0.0
        n1 = self.Nodes[0].Index
        n2 = self.Nodes[1].Index
        v1 = float(solutionVector[n1]) if n1 is not None else 0.0
        v2 = float(solutionVector[n2]) if n2 is not None else 0.0
        return v1 - v2

    def _limit_voltage(self, Vd_new: float, Vd_old: float) -> float:
        """
        SPICE-style PN-junction voltage limiting.

        Prevents the Newton step from proposing excessively large
        forward-bias voltages that would cause ``exp()`` overflow.
        """
        nVt = self._n * self._Vt
        Vcrit = self._Vcrit

        if Vd_new > Vcrit and abs(Vd_new - Vd_old) > 2.0 * nVt:
            # Logarithmic compression
            if Vd_old > 0.0:
                arg = 1.0 + (Vd_new - Vd_old) / nVt
                if arg > 0.0:
                    Vd_new = Vd_old + nVt * math.log(arg)
                else:
                    Vd_new = Vcrit
            else:
                Vd_new = nVt * math.log(Vd_new / nVt)
        # Clamp extremely negative voltages (reverse bias — not critical
        # but keeps things tidy)
        if Vd_new < -5.0 * self._Vcrit:
            Vd_new = -5.0 * self._Vcrit

        return Vd_new

    def _safe_exp(self, x: float) -> float:
        """``exp(x)`` clamped to prevent overflow."""
        return math.exp(min(x, self._EXP_MAX))

    def _evaluate(self, Vd: float) -> tuple[float, float]:
        """
        Evaluate diode current and conductance at operating point *Vd*.

        Returns ``(I_d, G_d)`` where::

            I_d = I_s · (exp(V_d / (n·V_t)) − 1)
            G_d = I_s / (n·V_t) · exp(V_d / (n·V_t))

        A small minimum conductance ``G_min = I_s / (n·V_t)`` is
        enforced so that the Jacobian never has a zero diagonal
        contribution from the diode in deep reverse bias.
        """
        nVt = self._n * self._Vt
        e = self._safe_exp(Vd / nVt)

        Id = self._Is * (e - 1.0)
        Gd = (self._Is / nVt) * e

        # Floor conductance so the diagonal never drops to zero
        Gd = max(Gd, self._Is / nVt)

        return Id, Gd

    # ── stamp ───────────────────────────────────────────────────────
    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        """
        Stamp the Newton-Raphson companion model into the MNA system.

        During NR iteration (``context.is_nonlinear_iteration`` is
        ``True`` and ``context.x_current`` is not ``None``), the
        diode linearises around the current guess.  Otherwise it
        stamps around the stored previous voltage.

        Companion model::

            I_d ≈ G_d · V_d + I_eq
            where  I_eq = I_d(V_d0) − G_d · V_d0

        ``G_d`` is stamped identically to a resistor, and ``I_eq`` is
        stamped as a current source entering the anode/leaving the
        cathode.
        """
        # --- determine operating-point voltage -----------------------
        if context.x_current is not None:
            Vd0 = self._get_vd(context.x_current)
        else:
            Vd0 = self._v_prev

        # Apply voltage limiting — reference is the *NR-tracked* voltage
        # during iteration, or the converged value otherwise.
        if context.is_nonlinear_iteration:
            Vd_ref = self._v_nr_prev
        else:
            Vd_ref = self._v_prev

        Vd0 = self._limit_voltage(Vd0, Vd_ref)

        # Update NR tracking so the next iteration limits relative to
        # this (already-limited) voltage rather than the previous step's.
        if context.is_nonlinear_iteration:
            self._v_nr_prev = Vd0

        Id0, Gd = self._evaluate(Vd0)

        # Equivalent current source: I_eq = Id0 - Gd * Vd0
        Ieq = Id0 - Gd * Vd0

        # --- stamp conductance Gd (same pattern as a resistor) ------
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
        # KCL:  current leaving node is positive in the MNA convention,
        # so I_eq flowing from anode to cathode *subtracts* from anode
        # and *adds* to cathode in the b vector.
        if n1 is not None:
            b[n1] -= Ieq
        if n2 is not None:
            b[n2] += Ieq

    # ── state update ────────────────────────────────────────────────
    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        """Store the converged diode voltage for the next NR sweep."""
        Vd = self._get_vd(solutionVector)
        Id, _ = self._evaluate(Vd)
        self._v_prev = Vd
        self._v_nr_prev = Vd     # reset NR reference for next sweep
        self._current = Id

    # ── query helpers ───────────────────────────────────────────────
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """Return diode current (anode → cathode, A)."""
        return self._current

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return voltage across the diode ``V(anode) − V(cathode)``."""
        return self._get_vd(solutionVector)
