"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.LiveSimulation' is deprecated. Use 'from PyEEL import LiveSimulation' instead.",
    DeprecationWarning, stacklevel=2,
)
from .Visualization.LiveSimulation import LiveSimulation  # noqa: F401, E402
__all__ = ["LiveSimulation"]
