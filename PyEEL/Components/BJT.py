"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.Components.BJT' is deprecated. Use 'from PyEEL import BJT' instead.",
    DeprecationWarning, stacklevel=2,
)
from .Semiconductors.BJT import BJT, BJTType, NPN, PNP  # noqa: F401, E402
__all__ = ["BJT", "BJTType", "NPN", "PNP"]
