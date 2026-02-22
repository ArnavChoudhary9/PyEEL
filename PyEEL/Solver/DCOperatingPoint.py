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
                 has_nonlinear: bool):
        self._components = components
        self._node_manager = node_manager
        self._solver = linear_solver
        self._config = config
        self._has_nonlinear = has_nonlinear

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
        """Solve nonlinear DC point with NR + optional source stepping."""
        cfg = self._config
        n = self._node_manager.TotalUnknownCount
        x = np.zeros(n)

        dc_ctx = SimulationContext(
            Mode=SimulationMode.DC,
            Time=0.0,
            dt=0.0,
            x_prev=None,
            x_current=x,
            integration_method=cfg.integration_method,
            gmin=cfg.gmin,
            is_nonlinear_iteration=True,
            source_factor=1.0,
        )

        steps = cfg.source_stepping_steps if cfg.source_stepping_enabled else 1

        for s in range(1, steps + 1):
            factor = s / steps
            dc_ctx.source_factor = factor

            for iteration in range(cfg.nr_max_iterations):
                dc_ctx.Iteration = iteration
                dc_ctx.x_current = x

                A_dc = np.zeros((n, n))
                b_dc = np.zeros(n)
                for comp in self._components:
                    comp.Stamp(A_dc, b_dc, dc_ctx)

                nv = self._node_manager.VoltageUnknownCount
                for i in range(nv):
                    A_dc[i, i] += dc_ctx.gmin

                residual = A_dc @ x - b_dc
                r_norm = float(np.max(np.abs(residual)))

                if iteration > 0:
                    if (r_norm < cfg.nr_abs_tolerance
                            and prev_dx_norm < cfg.nr_abs_tolerance  # type: ignore
                            + cfg.nr_rel_tolerance * x_norm):  # type: ignore
                        break

                try:
                    dx = self._solver.Solve(A_dc, -residual)
                except Exception:
                    break

                if not np.all(np.isfinite(dx)):
                    break

                x = x + dx
                prev_dx_norm = float(np.max(np.abs(dx)))
                x_norm = max(float(np.max(np.abs(x))), 1.0)

                if (r_norm < cfg.nr_abs_tolerance
                        and prev_dx_norm < cfg.nr_abs_tolerance
                        + cfg.nr_rel_tolerance * x_norm):
                    break

        dc_ctx.is_nonlinear_iteration = False
        dc_ctx.source_factor = 1.0

        # Propagate solution into component states
        for comp in self._components:
            comp.UpdateState(x, dc_ctx)

        return x
