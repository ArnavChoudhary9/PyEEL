from enum import Enum
from dataclasses import dataclass
import numpy as np


class SimulationMode(Enum):
    """Possible analysis modes for the simulation engine."""
    DC = 1
    AC = 2
    TRANSIENT = 3


@dataclass
class SimulationContext:
    """
    Immutable snapshot of all information a component needs during
    a single simulation step.

    Attributes
    ----------
    Mode : SimulationMode
        The current analysis type (DC, AC, or TRANSIENT).
    Time : float
        Current simulation time in seconds.
    dt : float
        Time-step size in seconds.
    x_prev : np.ndarray | None
        Solution vector from the previous time-step (``None`` for the
        first step).
    Frequency : float | None
        Driving frequency for AC analysis.
    Iteration : int | None
        Newton–Raphson iteration counter (for non-linear solvers).
    G_min : float | None
        Minimum conductance added for numerical stability in DC analysis.
    """

    Mode: SimulationMode
    Time: float
    dt: float

    x_prev: np.ndarray | None = None
    Frequency: float | None = 0
    Iteration: int | None = 0
    G_min: float | None = 0
    