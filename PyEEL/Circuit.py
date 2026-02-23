"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.Circuit' is deprecated. Use 'from PyEEL import Circuit' instead.",
    DeprecationWarning, stacklevel=2,
)
from .Simulation.Circuit import Circuit  # noqa: F401, E402
__all__ = ["Circuit"]
