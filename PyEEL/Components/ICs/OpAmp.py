"""
Operational Amplifier — macro model for MNA simulation.

This module provides a practical op-amp model with three levels of
fidelity:

1. **Ideal** — infinite gain, infinite input impedance, zero output impedance.
   Use ``A_OL=1e9, R_in=1e12, R_out=0.0``.
2. **Linear** — finite gain, finite input/output impedance.
   Default parameters match a typical general-purpose op-amp (LM741-like).
3. **Saturating** — same as linear, but the output clips to
   ``[V_sat_neg, V_sat_pos]`` when the open-loop output would
   exceed the rails.

Terminals
---------
``nodes = (non_inverting_input, inverting_input, output)``

The output is single-ended, referenced to ground.

MNA Formulation
---------------
The op-amp is stamped as:

- **Input resistance** ``G_in = 1 / R_in`` between ``V+`` and ``V-``.
- **Controlled source + output resistance** via one auxiliary unknown
  ``I_aux`` (output branch current).

Linear-region KVL equation (auxiliary row):

    ``V_out - R_out · I_aux - A_OL · (V+ - V-) = 0``

KCL at output node:

    ``I_aux`` enters the output node.

When saturation is enabled and the output would exceed a rail, the
gain term is replaced by a clamped voltage:

    ``V_out - R_out · I_aux = V_sat``   (gain drops to zero)
"""

from __future__ import annotations

import numpy as np

from ...Core.Node import Node
from ...Core.NodeManager import NodeManager
from ...Core.SimulationContext import SimulationContext
from ..Component import Component


class OpAmp(Component):
    """
    Operational amplifier — voltage-feedback macro model.

    Parameters
    ----------
    name : str
        Component identifier (e.g. ``'U1'``).
    nodes : tuple[Node, Node, Node]
        ``(non_inverting_input, inverting_input, output)``
    A_OL : float
        Open-loop DC voltage gain.  Default ``200_000`` (~106 dB).
    R_in : float
        Differential input resistance (Ω).  Default ``2e6``.
    R_out : float
        Output resistance (Ω).  Default ``75.0``.
    V_sat_pos : float | None
        Positive output saturation voltage (V).  ``None`` disables
        saturation (purely linear model).  When set, the component
        becomes nonlinear and Newton–Raphson is required.
    V_sat_neg : float | None
        Negative output saturation voltage (V).  Defaults to
        ``-V_sat_pos`` when only ``V_sat_pos`` is given.
    """

    _A_OL: float
    _R_in: float
    _R_out: float
    _V_sat_pos: float | None
    _V_sat_neg: float | None
    _saturating: bool
    _v_out_prev: float

    def __init__(
        self,
        name: str,
        nodes: tuple[Node, Node, Node],
        *,
        A_OL: float = 200_000.0,
        R_in: float = 2e6,
        R_out: float = 75.0,
        V_sat_pos: float | None = None,
        V_sat_neg: float | None = None,
    ):
        if len(nodes) != 3:
            raise ValueError(
                f"OpAmp '{name}' requires exactly 3 nodes "
                f"(inp, inn, out), got {len(nodes)}."
            )
        super().__init__(name, nodes)

        self._A_OL = A_OL
        self._R_in = R_in
        self._R_out = R_out

        # Saturation setup
        self._V_sat_pos = V_sat_pos
        if V_sat_neg is not None:
            self._V_sat_neg = V_sat_neg
        elif V_sat_pos is not None:
            self._V_sat_neg = -V_sat_pos
        else:
            self._V_sat_neg = None

        self._saturating = V_sat_pos is not None
        self._v_out_prev = 0.0

    # ── Properties ──────────────────────────────────────────────────

    @property
    def OpenLoopGain(self) -> float:
        """Open-loop DC voltage gain ``A_OL``."""
        return self._A_OL

    @property
    def InputResistance(self) -> float:
        """Differential input resistance ``R_in`` (Ω)."""
        return self._R_in

    @property
    def OutputResistance(self) -> float:
        """Output resistance ``R_out`` (Ω)."""
        return self._R_out

    @property
    def SaturationPositive(self) -> float | None:
        """Positive saturation voltage, or ``None``."""
        return self._V_sat_pos

    @property
    def SaturationNegative(self) -> float | None:
        """Negative saturation voltage, or ``None``."""
        return self._V_sat_neg

    @property
    def IsNonlinear(self) -> bool:
        return self._saturating

    # ── Abstract method implementations ─────────────────────────────

    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        # One auxiliary unknown for the output branch current.
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

        # ---- 1. Input resistance (G_in between V+ and V-) ----
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

        # ---- 3. KVL row (auxiliary equation) ----
        if self._saturating:
            self._stamp_saturating(A, b, context, inp_idx, inn_idx, out_idx, aux)
        else:
            self._stamp_linear(A, b, inp_idx, inn_idx, out_idx, aux)

    # ................................................................

    def _stamp_linear(
        self,
        A: np.ndarray,
        b: np.ndarray,
        inp_idx: int | None,
        inn_idx: int | None,
        out_idx: int | None,
        aux: int,
    ) -> None:
        """
        Stamp the purely-linear KVL equation:

            V_out - R_out · I_aux - A_OL · (V+ - V-) = 0
        """
        if out_idx is not None:
            A[aux, out_idx] += 1.0
        if self._R_out != 0.0:
            A[aux, aux] -= self._R_out
        if inp_idx is not None:
            A[aux, inp_idx] -= self._A_OL
        if inn_idx is not None:
            A[aux, inn_idx] += self._A_OL

    def _stamp_saturating(
        self,
        A: np.ndarray,
        b: np.ndarray,
        context: SimulationContext,
        inp_idx: int | None,
        inn_idx: int | None,
        out_idx: int | None,
        aux: int,
    ) -> None:
        """
        Piecewise-linear stamp with output-voltage clamping.

        * **Linear region** (``V_sat_neg < A_OL·Vdiff < V_sat_pos``):
          same as :meth:`_stamp_linear`.
        * **Positive saturation**: ``V_out - R_out · I_aux = V_sat_pos``
        * **Negative saturation**: ``V_out - R_out · I_aux = V_sat_neg``
        """
        # Current operating point
        v_inp = 0.0
        v_inn = 0.0
        if context.x_current is not None:
            if inp_idx is not None:
                v_inp = float(context.x_current[inp_idx])
            if inn_idx is not None:
                v_inn = float(context.x_current[inn_idx])

        v_diff = v_inp - v_inn
        v_ideal = self._A_OL * v_diff

        if v_ideal > self._V_sat_pos:                 # type: ignore[operator]
            # Positive saturation: V_out - R_out·I = V_sat_pos
            if out_idx is not None:
                A[aux, out_idx] += 1.0
            if self._R_out != 0.0:
                A[aux, aux] -= self._R_out
            b[aux] += self._V_sat_pos                  # type: ignore[operator]

        elif v_ideal < self._V_sat_neg:                # type: ignore[operator]
            # Negative saturation: V_out - R_out·I = V_sat_neg
            if out_idx is not None:
                A[aux, out_idx] += 1.0
            if self._R_out != 0.0:
                A[aux, aux] -= self._R_out
            b[aux] += self._V_sat_neg                  # type: ignore[operator]

        else:
            # Linear region
            self._stamp_linear(A, b, inp_idx, inn_idx, out_idx, aux)

    # ................................................................

    def UpdateState(
        self,
        solutionVector: np.ndarray,
        context: SimulationContext,
    ) -> None:
        out_idx = self.Nodes[2].Index
        self._v_out_prev = (
            float(solutionVector[out_idx]) if out_idx is not None else 0.0
        )

    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """Return the output branch current ``I_out``."""
        return float(solutionVector[self.AuxIndices[0]])

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return the output voltage ``V_out``."""
        out_idx = self.Nodes[2].Index
        return float(solutionVector[out_idx]) if out_idx is not None else 0.0

    # ── Convenience query methods ───────────────────────────────────

    def GetDifferentialInput(self, solutionVector: np.ndarray) -> float:
        """Return ``V+ - V-``."""
        inp_idx = self.Nodes[0].Index
        inn_idx = self.Nodes[1].Index
        v_p = float(solutionVector[inp_idx]) if inp_idx is not None else 0.0
        v_n = float(solutionVector[inn_idx]) if inn_idx is not None else 0.0
        return v_p - v_n

    def __repr__(self) -> str:
        return (
            f"OpAmp({self.Name!r}, A_OL={self._A_OL:.0f}, "
            f"R_in={self._R_in:.0e}, R_out={self._R_out:.1f})"
        )
