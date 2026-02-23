"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.Components.Capacitor' is deprecated. Use 'from PyEEL import Capacitor' instead.",
    DeprecationWarning, stacklevel=2,
)
from .Passive.Capacitor import Capacitor  # noqa: F401, E402
__all__ = ["Capacitor"]
