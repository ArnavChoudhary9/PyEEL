"""
Simulation configuration and per-step context.

:class:`SimulationConfig` holds tunable knobs for the simulation engine
(tolerances, integration method, adaptive-timestep settings, etc.).

:class:`SimulationContext` is a lightweight snapshot passed to every
component's :meth:`Stamp` and :meth:`UpdateState` during a single step.
"""

from enum import Enum
from dataclasses import dataclass
import numpy as np


class SimulationMode(Enum):
    """Possible analysis modes for the simulation engine."""
    DC = 1
    AC = 2
    TRANSIENT = 3


class IntegrationMethod(Enum):
    """
    Time-stepping integration methods.

    BACKWARD_EULER — first-order, unconditionally stable, diffusive.
                     Use this initially; it is the safest default.
    TRAPEZOIDAL    — second-order, less diffusive but can oscillate
                     on stiff systems.  Enable only after the engine
                     is verified stable with Backward Euler.
    """
    BACKWARD_EULER = 1
    TRAPEZOIDAL = 2


@dataclass
class SimulationConfig:
    """
    Global simulation configuration parameters.

    Controls numerical-stability knobs, integration method, time-step
    bounds, and optional runtime diagnostics.  Passed to :class:`Circuit`
    at construction time; individual fields are forwarded to every
    :class:`SimulationContext` created during the run.
    """

    # ── integration ─────────────────────────────────────────────────
    integration_method: IntegrationMethod = IntegrationMethod.BACKWARD_EULER
    gmin: float = 1e-12

    # ── time-step bounds ────────────────────────────────────────────
    min_dt: float = 1e-15
    max_dt: float = 1.0

    # ── DC operating point ──────────────────────────────────────────
    dc_operating_point: bool = True
    dc_inductor_resistance: float = 1e-9

    # ── adaptive timestep ───────────────────────────────────────────
    adaptive_timestep: bool = False
    adaptive_threshold: float = 0.5
    adaptive_shrink: float = 0.5
    adaptive_grow: float = 1.05
    max_grow_factor: float = 2.0

    # ── diagnostics ─────────────────────────────────────────────────
    condition_number_warning: float = 1e15
    energy_check: bool = True
    max_energy: float = 1e12

    # ── Newton-Raphson convergence ──────────────────────────────────
    nr_max_iterations: int = 50
    nr_abs_tolerance: float = 1e-9
    nr_rel_tolerance: float = 1e-6
    nr_damping_enabled: bool = True
    nr_initial_damping: float = 1.0
    nr_min_damping: float = 0.01
    nr_vt_limit: float = 0.025 * 10  # ~10×V_T for PN junction limiting

    # ── Gmin stepping (fallback) ───────────────────────────────────
    gmin_stepping_enabled: bool = True
    gmin_stepping_start: float = 1e-3
    gmin_stepping_factor: float = 10.0
    gmin_stepping_min: float = 1e-12

    # ── Source stepping (fallback) ─────────────────────────────────
    source_stepping_enabled: bool = True
    source_stepping_steps: int = 10

    # ── Temperature ─────────────────────────────────────────────────
    temperature: float = 300.15  # kelvin (≈ 27 °C = SPICE default)


@dataclass
class SimulationContext:
    """
    Snapshot of everything a component needs during a single
    simulation step.

    Attributes
    ----------
    Mode : SimulationMode
        Current analysis type (DC, AC, or TRANSIENT).
    Time : float
        Simulation time in seconds.
    dt : float
        Time-step size in seconds.
    x_prev : np.ndarray | None
        Solution vector from the previous time-step.
    x_current : np.ndarray | None
        Current NR iterate (for nonlinear components).
    Frequency : float | None
        Driving frequency for AC analysis.
    Iteration : int
        Newton-Raphson iteration counter.
    is_nonlinear_iteration : bool
        ``True`` during NR sweeps.
    source_factor : float
        Scaling factor for source stepping (0 → 1).
    integration_method : IntegrationMethod
        Active integration rule.
    gmin : float
        Global minimum conductance (forwarded from SimulationConfig).
    """

    Mode: SimulationMode
    Time: float
    dt: float

    x_prev: np.ndarray | None = None
    x_current: np.ndarray | None = None
    Frequency: float | None = 0
    Iteration: int = 0
    is_nonlinear_iteration: bool = False
    source_factor: float = 1.0
    integration_method: IntegrationMethod = IntegrationMethod.BACKWARD_EULER
    gmin: float = 1e-12
    temperature: float = 300.15  # kelvin
