from enum import Enum
from dataclasses import dataclass
import numpy as np

class SimulationMode(Enum):
    DC = 1
    AC = 2
    TRANSIENT = 3

@dataclass
class SimulationContext:
    Mode: SimulationMode
    Time: float
    dt: float
    Frequency: float | None
    x_prev: np.ndarray
    Iteration: int | None
    G_min: float | None # Minimum conductance for numerical stability in DC analysis
    