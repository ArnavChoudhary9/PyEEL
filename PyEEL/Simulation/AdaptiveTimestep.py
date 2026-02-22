"""
Adaptive time-step heuristic.

Extracted from ``Circuit._update_recommended_dt`` / ``_clamp_dt`` to
honour the single-responsibility principle.
"""

from __future__ import annotations

import numpy as np

from ..Core.SimulationContext import SimulationConfig


class AdaptiveTimestep:
    """
    Computes a recommended *dt* for the next step based on how much
    the solution changed.

    Parameters
    ----------
    config : SimulationConfig
        Provides thresholds, growth/shrink factors, and dt limits.
    """

    def __init__(self, config: SimulationConfig):
        self._config = config
        self._recommended_dt: float | None = None

    @property
    def recommended_dt(self) -> float | None:
        """Last computed recommendation (``None`` if never called)."""
        return self._recommended_dt

    def clamp(self, dt: float) -> float:
        """Clamp *dt* to the configured ``[min_dt, max_dt]`` range."""
        return max(self._config.min_dt, min(dt, self._config.max_dt))

    def update(self, dt: float,
               solution: np.ndarray,
               x_prev: np.ndarray | None) -> None:
        """Compute the recommended *dt* for the next step."""
        if not self._config.adaptive_timestep or x_prev is None:
            self._recommended_dt = dt
            return

        dx_max = float(np.max(np.abs(solution - x_prev)))
        x_scale = max(float(np.max(np.abs(solution))), 1.0)
        relative_change = dx_max / x_scale

        cfg = self._config
        if relative_change > cfg.adaptive_threshold:
            self._recommended_dt = max(dt * cfg.adaptive_shrink,
                                       cfg.min_dt)
        elif relative_change < cfg.adaptive_threshold * 0.1:
            grow = min(cfg.adaptive_grow, cfg.max_grow_factor)
            self._recommended_dt = min(dt * grow, cfg.max_dt)
        else:
            self._recommended_dt = dt
