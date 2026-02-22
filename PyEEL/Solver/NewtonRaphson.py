"""
Newton-Raphson nonlinear solver.

Iterates until the dual convergence criteria are met:

  1. ``||Δx||_∞ < abs_tol + rel_tol × ||x||_∞``
  2. ``||F(x)||_∞ < abs_tol`` (residual)

Falls back to Gmin stepping on failure.
"""

from __future__ import annotations

import logging
import numpy as np

from ..Core.SimulationContext import SimulationConfig, SimulationContext
from .LinearSolver import LinearSolver
from .MNASystemBuilder import MNASystemBuilder

logger = logging.getLogger(__name__)


class NewtonRaphsonSolver:
    """
    Newton-Raphson iteration for circuits with nonlinear components.

    Parameters
    ----------
    system_builder : MNASystemBuilder
        Assembles the linearised MNA system each iteration.
    linear_solver : LinearSolver
        Solves the linear system ``J Δx = -F``.
    config : SimulationConfig
        Convergence tolerances and damping settings.
    """

    def __init__(self, system_builder: MNASystemBuilder,
                 linear_solver: LinearSolver,
                 config: SimulationConfig):
        self._builder = system_builder
        self._solver = linear_solver
        self._config = config

    def solve(self, context: SimulationContext) -> np.ndarray:
        """
        Perform Newton-Raphson iteration.

        Uses ``context.x_prev`` as the initial guess and mutates
        ``context.x_current`` / ``context.is_nonlinear_iteration``
        during the sweep.

        Returns the converged (or best-effort) solution vector.
        """
        cfg = self._config
        n = len(context.x_prev) if context.x_prev is not None else 0

        # Initial guess: previous timestep solution
        x = context.x_prev.copy() if context.x_prev is not None else np.zeros(n)

        context.is_nonlinear_iteration = True
        context.x_current = x

        converged = False
        dx_norm = float('inf')
        new_residual_norm = float('inf')

        for iteration in range(cfg.nr_max_iterations):
            context.Iteration = iteration
            context.x_current = x

            A, b = self._builder.build(context)

            # Residual: F(x) = A·x - b
            residual = A @ x - b
            residual_norm = float(np.max(np.abs(residual)))

            # Solve J·Δx = -F
            try:
                dx = self._solver.Solve(A, -residual)
            except Exception:
                logger.warning("NR iteration %d: linear solve failed.", iteration)
                break

            if not np.all(np.isfinite(dx)):
                logger.warning("NR iteration %d: dx contains NaN/Inf.", iteration)
                break

            # Damping (line search)
            alpha = cfg.nr_initial_damping
            if cfg.nr_damping_enabled:
                x_trial = x + alpha * dx
                context.x_current = x_trial
                A_trial, b_trial = self._builder.build(context)
                r_trial = float(np.max(np.abs(A_trial @ x_trial - b_trial)))

                attempts = 0
                while r_trial > residual_norm and alpha > cfg.nr_min_damping and attempts < 10:
                    alpha *= 0.5
                    x_trial = x + alpha * dx
                    context.x_current = x_trial
                    A_trial, b_trial = self._builder.build(context)
                    r_trial = float(np.max(np.abs(A_trial @ x_trial - b_trial)))
                    attempts += 1

            x_new = x + alpha * dx

            # Convergence check (dual criteria)
            dx_norm = float(np.max(np.abs(alpha * dx)))
            x_norm = max(float(np.max(np.abs(x_new))), 1.0)
            update_converged = dx_norm < (cfg.nr_abs_tolerance + cfg.nr_rel_tolerance * x_norm)

            # Recompute residual at new point
            context.x_current = x_new
            A_new, b_new = self._builder.build(context)
            new_residual_norm = float(np.max(np.abs(A_new @ x_new - b_new)))
            residual_converged = new_residual_norm < cfg.nr_abs_tolerance

            x = x_new

            if update_converged and residual_converged:
                converged = True
                break

        context.is_nonlinear_iteration = False

        if not converged:
            # Fallback: Gmin stepping
            if cfg.gmin_stepping_enabled:
                x_gmin = self._gmin_stepping_solve(context)
                if x_gmin is not None:
                    return x_gmin

            logger.warning(
                "Newton-Raphson did not converge in %d iterations "
                "(dx=%.2e, residual=%.2e). Using last iterate.",
                cfg.nr_max_iterations, dx_norm, new_residual_norm,
            )

        return x

    def _gmin_stepping_solve(self, context: SimulationContext) -> np.ndarray | None:
        """
        Gmin-stepping fallback: start with artificially large Gmin and
        gradually reduce it to normal levels.
        """
        cfg = self._config
        n = len(context.x_prev) if context.x_prev is not None else 0
        x = context.x_prev.copy() if context.x_prev is not None else np.zeros(n)

        gmin_val = cfg.gmin_stepping_start
        original_gmin = context.gmin

        logger.info("Attempting Gmin stepping (start=%.2e)...", gmin_val)

        while gmin_val >= cfg.gmin_stepping_min:
            context.gmin = gmin_val
            self._builder.gmin = gmin_val
            context.x_current = x
            context.is_nonlinear_iteration = True

            inner_converged = False
            for iteration in range(cfg.nr_max_iterations):
                context.Iteration = iteration
                context.x_current = x

                A, b = self._builder.build(context)
                residual = A @ x - b
                residual_norm = float(np.max(np.abs(residual)))

                try:
                    dx = self._solver.Solve(A, -residual)
                except Exception:
                    break

                if not np.all(np.isfinite(dx)):
                    break

                x = x + dx
                dx_norm = float(np.max(np.abs(dx)))
                x_norm = max(float(np.max(np.abs(x))), 1.0)

                if (dx_norm < cfg.nr_abs_tolerance + cfg.nr_rel_tolerance * x_norm
                        and residual_norm < cfg.nr_abs_tolerance):
                    inner_converged = True
                    break

            if not inner_converged:
                context.gmin = original_gmin
                self._builder.gmin = original_gmin
                context.is_nonlinear_iteration = False
                logger.warning("Gmin stepping failed at gmin=%.2e", gmin_val)
                return None

            gmin_val /= cfg.gmin_stepping_factor

        context.gmin = original_gmin
        self._builder.gmin = original_gmin
        context.is_nonlinear_iteration = False
        logger.info("Gmin stepping converged.")
        return x
