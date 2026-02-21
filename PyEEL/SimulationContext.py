from enum import Enum
from dataclasses import dataclass, field
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

    Attributes
    ----------
    integration_method : IntegrationMethod
        Time integration scheme.  Default is Backward Euler.
    gmin : float
        Minimum conductance (S) added from every voltage node to ground.
        Prevents singular matrices from floating nodes.  1e-12 is the
        SPICE standard.
    min_dt : float
        Minimum allowed time-step (s).  Prevents machine-precision disasters.
    max_dt : float
        Maximum allowed time-step (s).
    dc_operating_point : bool
        Solve a DC operating-point before the first transient step and
        use the result as initial conditions.
    adaptive_timestep : bool
        Enable basic adaptive time-step control.
    adaptive_threshold : float
        Maximum allowed *relative* solution change per step before the
        engine recommends shrinking dt.
    adaptive_shrink : float
        Multiply dt by this factor when the solution changes too fast.
    adaptive_grow : float
        Multiply dt by this factor when the solution is smooth.
    max_grow_factor : float
        Upper bound on the growth ratio (caps runaway growth).
    condition_number_warning : float
        Warn if ``cond(A)`` exceeds this value.
    energy_check : bool
        Periodically verify that energy stored in L/C components
        remains finite and below *max_energy*.
    max_energy : float
        Per-component energy threshold (J) for the sanity check.
    dc_inductor_resistance : float
        Small resistance (Ω) used to model inductors as short circuits
        during DC operating-point analysis.
    """
    integration_method: IntegrationMethod = IntegrationMethod.BACKWARD_EULER
    gmin: float = 1e-12

    min_dt: float = 1e-15
    max_dt: float = 1.0

    dc_operating_point: bool = True

    adaptive_timestep: bool = False
    adaptive_threshold: float = 0.5
    adaptive_shrink: float = 0.5
    adaptive_grow: float = 1.05
    max_grow_factor: float = 2.0

    condition_number_warning: float = 1e15
    energy_check: bool = True
    max_energy: float = 1e12

    dc_inductor_resistance: float = 1e-9


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
        Solution vector from the previous time-step (``None`` on the
        first step).
    Frequency : float | None
        Driving frequency for AC analysis.
    Iteration : int | None
        Newton-Raphson iteration counter (future non-linear solvers).
    integration_method : IntegrationMethod
        Which integration rule is active this step.
    gmin : float
        Global minimum conductance (forwarded from SimulationConfig).
    """

    Mode: SimulationMode
    Time: float
    dt: float

    x_prev: np.ndarray | None = None
    Frequency: float | None = 0
    Iteration: int | None = 0
    integration_method: IntegrationMethod = IntegrationMethod.BACKWARD_EULER
    gmin: float = 1e-12
    