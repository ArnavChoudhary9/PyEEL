"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.Components.Comparator' is deprecated. Use 'from PyEEL import Comparator' instead.",
    DeprecationWarning, stacklevel=2,
)
from .ICs.Comparator import Comparator  # noqa: F401, E402
__all__ = ["Comparator"]
