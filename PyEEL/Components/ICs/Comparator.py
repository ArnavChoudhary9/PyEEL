"""
Voltage Comparator — macro model for MNA simulation.

A comparator switches its output rail-to-rail based on the sign of the
differential input ``(V+ - V-)``, optionally with hysteresis.

Terminals
---------
``nodes = (non_inverting_input, inverting_input, output)``

MNA Formulation
---------------
The comparator is stamped as a **voltage-controlled voltage source** that
is always clamped to one of two discrete levels:

- **High state** (``V+ - V- > +V_hys/2``): ``V_out - R_out·I_aux = V_high``
- **Low state**  (``V+ - V- < -V_hys/2``): ``V_out - R_out·I_aux = V_low``
- **Within hysteresis band**: previous output state is held.

This is inherently nonlinear (``IsNonlinear = True``); the output state is
re-evaluated every Newton–Raphson iteration from ``context.x_current``.

Hysteresis
----------
When ``V_hys > 0``, the comparator implements a **Schmitt trigger** with:

- ``V_trip_high = +V_hys / 2``  (rising threshold)
- ``V_trip_low  = -V_hys / 2``  (falling threshold)

The output state transitions only when the differential crosses the
*opposite* threshold, providing noise immunity.
"""

from __future__ import annotations

import numpy as np

from ...Core.Node import Node
from ...Core.NodeManager import NodeManager
from ...Core.SimulationContext import SimulationContext
from ..Component import Component


class Comparator(Component):
    """
    Voltage comparator macro model.

    Parameters
    ----------
    name : str
        Component identifier (e.g. ``'U2'``).
    nodes : tuple[Node, Node, Node]
        ``(non_inverting_input, inverting_input, output)``
    V_high : float
        Output high voltage (V).  Default ``5.0``.
    V_low : float
        Output low voltage (V).  Default ``0.0``.
    V_hys : float
        Total hysteresis band width (V).  Default ``0.0`` (no hysteresis).
        Trip points are at ``±V_hys/2``.
    R_in : float
        Differential input resistance (Ω).  Default ``1e6``.
    R_out : float
        Output resistance (Ω).  Default ``50.0``.
    initial_state_high : bool
        Starting output state before the first NR evaluation.
        Default ``True`` (output starts high).
    """

    _V_high: float
    _V_low: float
    _V_hys: float
    _R_in: float
    _R_out: float
    _state_high: bool     # True = output is currently HIGH

    def __init__(
        self,
        name: str,
        nodes: tuple[Node, Node, Node],
        *,
        V_high: float = 5.0,
        V_low: float = 0.0,
        V_hys: float = 0.0,
        R_in: float = 1e6,
        R_out: float = 50.0,
        initial_state_high: bool = True,
    ):
        if len(nodes) != 3:
            raise ValueError(
                f"Comparator '{name}' requires exactly 3 nodes "
                f"(inp, inn, out), got {len(nodes)}."
            )
        super().__init__(name, nodes)

        self._V_high = V_high
        self._V_low = V_low
        self._V_hys = V_hys
        self._R_in = R_in
        self._R_out = R_out
        self._state_high = initial_state_high

    # ── Properties ──────────────────────────────────────────────────

    @property
    def OutputHigh(self) -> float:
        """Configured high output voltage ``V_high`` (V)."""
        return self._V_high

    @property
    def OutputLow(self) -> float:
        """Configured low output voltage ``V_low`` (V)."""
        return self._V_low

    @property
    def Hysteresis(self) -> float:
        """Hysteresis band width ``V_hys`` (V)."""
        return self._V_hys

    @property
    def InputResistance(self) -> float:
        """Differential input resistance ``R_in`` (Ω)."""
        return self._R_in

    @property
    def OutputResistance(self) -> float:
        """Output resistance ``R_out`` (Ω)."""
        return self._R_out

    @property
    def IsStateHigh(self) -> bool:
        """``True`` when the comparator output is currently in the HIGH state."""
        return self._state_high

    @property
    def IsNonlinear(self) -> bool:
        return True

    # ── Abstract method implementations ─────────────────────────────

    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        self._aux_indices.append(nodeManager.RequestAuxiliaryUnknown())

    def Stamp(
        self,
        A: np.ndarray,
        b: np.ndarray,
        context: SimulationContext,
    ) -> None:
        inp_idx = self.Nodes[0].Index   # V+ (non-inverting)
        inn_idx = self.Nodes[1].Index   # V- (inverting)
        out_idx = self.Nodes[2].Index   # output
        aux = self.AuxIndices[0]        # I_out branch current

        # ---- 1. Input resistance between V+ and V- ----
        if self._R_in > 0.0:
            G_in = 1.0 / self._R_in
            if inp_idx is not None:
                A[inp_idx, inp_idx] += G_in
                if inn_idx is not None:
                    A[inp_idx, inn_idx] -= G_in
            if inn_idx is not None:
                A[inn_idx, inn_idx] += G_in
                if inp_idx is not None:
                    A[inn_idx, inp_idx] -= G_in

        # ---- 2. KCL: branch current enters output node ----
        if out_idx is not None:
            A[out_idx, aux] += 1.0

        # ---- 3. Determine output state from current operating point ----
        v_inp = 0.0
        v_inn = 0.0
        if context.x_current is not None:
            if inp_idx is not None:
                v_inp = float(context.x_current[inp_idx])
            if inn_idx is not None:
                v_inn = float(context.x_current[inn_idx])

        v_diff = v_inp - v_inn
        half_hys = self._V_hys * 0.5

        if v_diff > half_hys:
            self._state_high = True
        elif v_diff < -half_hys:
            self._state_high = False
        # else: within dead-band → keep previous state (hysteresis)

        v_target = self._V_high if self._state_high else self._V_low

        # ---- 4. KVL row: V_out - R_out·I_aux = V_target ----
        if out_idx is not None:
            A[aux, out_idx] += 1.0
        if self._R_out != 0.0:
            A[aux, aux] -= self._R_out
        b[aux] += v_target

    def UpdateState(
        self,
        solutionVector: np.ndarray,
        context: SimulationContext,
    ) -> None:
        # State is maintained in _state_high, updated during Stamp.
        # Re-evaluate from the converged solution vector for accuracy.
        inp_idx = self.Nodes[0].Index
        inn_idx = self.Nodes[1].Index
        v_inp = float(solutionVector[inp_idx]) if inp_idx is not None else 0.0
        v_inn = float(solutionVector[inn_idx]) if inn_idx is not None else 0.0
        v_diff = v_inp - v_inn
        half_hys = self._V_hys * 0.5

        if v_diff > half_hys:
            self._state_high = True
        elif v_diff < -half_hys:
            self._state_high = False

    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """Return the output branch current ``I_out``."""
        return float(solutionVector[self.AuxIndices[0]])

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return the output voltage ``V_out``."""
        out_idx = self.Nodes[2].Index
        return float(solutionVector[out_idx]) if out_idx is not None else 0.0

    def GetDifferentialInput(self, solutionVector: np.ndarray) -> float:
        """Return ``V+ - V-``."""
        inp_idx = self.Nodes[0].Index
        inn_idx = self.Nodes[1].Index
        v_p = float(solutionVector[inp_idx]) if inp_idx is not None else 0.0
        v_n = float(solutionVector[inn_idx]) if inn_idx is not None else 0.0
        return v_p - v_n

    def __repr__(self) -> str:
        state = "HIGH" if self._state_high else "LOW"
        return (
            f"Comparator({self.Name!r}, "
            f"V_high={self._V_high}, V_low={self._V_low}, "
            f"V_hys={self._V_hys}, state={state})"
        )
