"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.Components.Inductor' is deprecated. Use 'from PyEEL import Inductor' instead.",
    DeprecationWarning, stacklevel=2,
)
from .Passive.Inductor import Inductor  # noqa: F401, E402
__all__ = ["Inductor"]
