"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.Components.MOSFET' is deprecated. Use 'from PyEEL import MOSFET' instead.",
    DeprecationWarning, stacklevel=2,
)
from .Semiconductors.MOSFET import MOSFET, MOSFETType, NMOS, PMOS  # noqa: F401, E402
__all__ = ["MOSFET", "MOSFETType", "NMOS", "PMOS"]
