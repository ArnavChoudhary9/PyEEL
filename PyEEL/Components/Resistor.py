"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.Components.Resistor' is deprecated. Use 'from PyEEL import Resistor' instead.",
    DeprecationWarning, stacklevel=2,
)
from .Passive.Resistor import Resistor  # noqa: F401, E402
__all__ = ["Resistor"]
