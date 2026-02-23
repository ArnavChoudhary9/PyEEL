"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.Components.OpAmp' is deprecated. Use 'from PyEEL import OpAmp' instead.",
    DeprecationWarning, stacklevel=2,
)
from .ICs.OpAmp import OpAmp  # noqa: F401, E402
__all__ = ["OpAmp"]
