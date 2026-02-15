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
    
    x_prev: np.ndarray | None = None
    Frequency: float | None = 0
    Iteration: int | None = 0
    G_min: float | None = 0 # Minimum conductance for numerical stability in DC analysis
    