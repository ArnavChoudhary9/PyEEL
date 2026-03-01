"""
Scope sub-package — oscilloscope-style visualization for PyEEL.

Quick start::

    from PyEEL.Visualization.Scope import Scope

    scope = Scope([v_probe], [i_probe], window=0.02)
    # ... simulation loop ...
    scope.Update()

Drop-in replacement for :class:`LivePlotter` — same ``Update()``,
``Close()``, ``KeepOpen()``, ``IsOpen`` interface.
"""

from .Scope import Scope
from ._buffer import CircularBuffer
from ._channel import ScopeChannel
from ._trigger import Trigger, TriggerEdge, TriggerMode, TriggerState
from ._measurements import compute_measurements, MeasurementResult
from ._renderer import ScopeRenderer

__all__ = [
    "Scope",
    "CircularBuffer",
    "ScopeChannel",
    "Trigger",
    "TriggerEdge",
    "TriggerMode",
    "TriggerState",
    "ScopeRenderer",
    "compute_measurements",
    "MeasurementResult",
]
