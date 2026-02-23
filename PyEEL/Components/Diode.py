"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.Components.Diode' is deprecated. Use 'from PyEEL import Diode' instead.",
    DeprecationWarning, stacklevel=2,
)
from .Semiconductors.Diode import Diode  # noqa: F401, E402
__all__ = ["Diode"]
