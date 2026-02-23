"""
DC operating-point solver.

Computes the DC bias point of a circuit by:

- **Linear circuits**: single matrix solve with capacitors open and
  inductors shorted.
- **Nonlinear circuits**: Newton-Raphson iteration with optional
  source stepping.
"""

from __future__ import annotations

import logging
import numpy as np

from ..Core.NodeManager import NodeManager
from ..Core.SimulationContext import (
    SimulationConfig, SimulationContext, SimulationMode,
)
from ..Components.Component import Component
from .LinearSolver import LinearSolver

logger = logging.getLogger(__name__)


class DCOperatingPointSolver:
    """
    Solves the DC operating point of a circuit.

    Parameters
    ----------
    components : list[Component]
        All circuit components.
    node_manager : NodeManager
        Node index allocator.
    linear_solver : LinearSolver
        Dense/sparse solver for ``Ax = b``.
    config : SimulationConfig
        Convergence and stepping parameters.
    has_nonlinear : bool
        Whether the circuit contains nonlinear components.
    """

    def __init__(self, components: list[Component],
                 node_manager: NodeManager,
                 linear_solver: LinearSolver,
                 config: SimulationConfig,
                 has_nonlinear: bool,
                 initial_guesses: dict[int, float] | None = None):
        self._components = components
        self._node_manager = node_manager
        self._solver = linear_solver
        self._config = config
        self._has_nonlinear = has_nonlinear
        self._initial_guesses = initial_guesses or {}

    def solve(self) -> np.ndarray:
        """
        Solve the DC operating point and return the solution vector.

        For nonlinear circuits, uses Newton-Raphson with optional source
        stepping.  For linear circuits, a single direct solve.
        """
        cfg = self._config
        n = self._node_manager.TotalUnknownCount

        if self._has_nonlinear:
            try:
                x_dc = self._solve_nonlinear()
                logger.info("Nonlinear DC operating point solved successfully.")
                return x_dc
            except Exception as exc:
                logger.warning(
                    "Nonlinear DC OP solve failed (%s). "
                    "Starting from zero initial conditions.", exc,
                )
                return np.zeros(n)

        return self._solve_linear()

    def _solve_linear(self) -> np.ndarray:
        """Solve linear DC operating point with a single matrix solve."""
        cfg = self._config
        n = self._node_manager.TotalUnknownCount

        A_dc = np.zeros((n, n))
        b_dc = np.zeros(n)

        dc_context = SimulationContext(
            Mode=SimulationMode.DC,
            Time=0.0,
            dt=0.0,
            x_prev=None,
            integration_method=cfg.integration_method,
            gmin=cfg.gmin,
        )

        for comp in self._components:
            comp.Stamp(A_dc, b_dc, dc_context)

        # Gmin on every voltage node
        gmin = cfg.gmin
        nv = self._node_manager.VoltageUnknownCount
        for i in range(nv):
            A_dc[i, i] += gmin

        try:
            x_dc = self._solver.Solve(A_dc, b_dc)

            # Propagate DC solution into component states
            for comp in self._components:
                comp.UpdateState(x_dc, dc_context)

            logger.info("DC operating point solved successfully.")
            return x_dc

        except Exception as exc:
            logger.warning(
                "DC operating point solve failed (%s). "
                "Starting transient from zero initial conditions.",
                exc,
            )
            return np.zeros(self._node_manager.TotalUnknownCount)

    def _solve_nonlinear(self) -> np.ndarray:
        """
        Solve nonlinear DC point with a robust homotopy chain:

        1. Direct NR (no stepping)
        2. Source stepping (ramp source_factor 0→1)
        3. Gmin stepping (start high, reduce to normal)
        4. Combined stepping (source + Gmin together)

        Each strategy is tried in order; the first to converge wins.
        """
        cfg = self._config
        n = self._node_manager.TotalUnknownCount
        x0 = np.zeros(n)

        # Inject user-supplied initial guesses
        for idx, val in self._initial_guesses.items():
            if 0 <= idx < n:
                x0[idx] = val

        # Strategy 1: Direct NR
        x, ok = self._nr_dc(x0.copy(), source_factor=1.0, gmin=cfg.gmin)
        if ok:
            logger.info("DC OP converged with direct NR.")
            self._finalize_dc(x)
            return x

        # Strategy 2: Source stepping
        if cfg.source_stepping_enabled:
            x_ss, ok = self._source_stepping(x0.copy())
            if ok:
                logger.info("DC OP converged with source stepping.")
                self._finalize_dc(x_ss)
                return x_ss

        # Strategy 3: Gmin stepping
        if cfg.gmin_stepping_enabled:
            x_gs, ok = self._gmin_stepping(x0.copy())
            if ok:
                logger.info("DC OP converged with Gmin stepping.")
                self._finalize_dc(x_gs)
                return x_gs

        # Strategy 4: Combined stepping (source + Gmin)
        if cfg.source_stepping_enabled and cfg.gmin_stepping_enabled:
            x_cs, ok = self._combined_stepping(x0.copy())
            if ok:
                logger.info("DC OP converged with combined stepping.")
                self._finalize_dc(x_cs)
                return x_cs

        logger.warning("All DC OP homotopy strategies failed. Using last iterate.")
        self._finalize_dc(x)
        return x

    def _finalize_dc(self, x: np.ndarray) -> None:
        """Propagate converged DC solution into component states."""
        dc_ctx = SimulationContext(
            Mode=SimulationMode.DC, Time=0.0, dt=0.0,
            x_prev=None, x_current=x,
            integration_method=self._config.integration_method,
            gmin=self._config.gmin,
        )
        for comp in self._components:
            comp.UpdateState(x, dc_ctx)

    def _nr_dc(self, x: np.ndarray, *, source_factor: float,
               gmin: float) -> tuple[np.ndarray, bool]:
        """Run NR iterations at fixed source_factor/gmin. Returns (x, converged)."""
        cfg = self._config
        n = len(x)
        nv = self._node_manager.VoltageUnknownCount

        dc_ctx = SimulationContext(
            Mode=SimulationMode.DC, Time=0.0, dt=0.0,
            x_prev=None, x_current=x,
            integration_method=cfg.integration_method,
            gmin=gmin,
            is_nonlinear_iteration=True,
            source_factor=source_factor,
        )

        for iteration in range(cfg.nr_max_iterations):
            dc_ctx.Iteration = iteration
            dc_ctx.x_current = x

            A_dc = np.zeros((n, n))
            b_dc = np.zeros(n)
            for comp in self._components:
                comp.Stamp(A_dc, b_dc, dc_ctx)
            for i in range(nv):
                A_dc[i, i] += gmin

            residual = A_dc @ x - b_dc
            r_norm = float(np.max(np.abs(residual)))

            try:
                dx = self._solver.Solve(A_dc, -residual)
            except Exception:
                return x, False

            if not np.all(np.isfinite(dx)):
                return x, False

            x = x + dx
            dx_norm = float(np.max(np.abs(dx)))
            x_norm = max(float(np.max(np.abs(x))), 1.0)

            if (r_norm < cfg.nr_abs_tolerance
                    and dx_norm < cfg.nr_abs_tolerance
                    + cfg.nr_rel_tolerance * x_norm):
                return x, True

        return x, False

    def _source_stepping(self, x: np.ndarray) -> tuple[np.ndarray, bool]:
        """Ramp source_factor from 1/N to 1 in N steps."""
        cfg = self._config
        steps = cfg.source_stepping_steps
        for s in range(1, steps + 1):
            factor = s / steps
            x, ok = self._nr_dc(x, source_factor=factor, gmin=cfg.gmin)
            if not ok:
                return x, False
        return x, True

    def _gmin_stepping(self, x: np.ndarray) -> tuple[np.ndarray, bool]:
        """Start with large Gmin and progressively reduce."""
        cfg = self._config
        gmin_val = cfg.gmin_stepping_start
        while gmin_val >= cfg.gmin_stepping_min:
            x, ok = self._nr_dc(x, source_factor=1.0, gmin=gmin_val)
            if not ok:
                return x, False
            gmin_val /= cfg.gmin_stepping_factor
        # Final solve at normal gmin
        x, ok = self._nr_dc(x, source_factor=1.0, gmin=cfg.gmin)
        return x, ok

    def _combined_stepping(self, x: np.ndarray) -> tuple[np.ndarray, bool]:
        """
        Combined homotopy: simultaneously ramp source_factor up
        and gmin down.
        """
        cfg = self._config
        steps = cfg.source_stepping_steps
        gmin_start = cfg.gmin_stepping_start
        gmin_end = cfg.gmin

        for s in range(1, steps + 1):
            t = s / steps
            factor = t
            gmin_val = gmin_start * (gmin_end / gmin_start) ** t
            x, ok = self._nr_dc(x, source_factor=factor, gmin=gmin_val)
            if not ok:
                return x, False
        return x, True
