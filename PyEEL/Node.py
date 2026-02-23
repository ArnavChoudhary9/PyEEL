"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.Node' is deprecated. Use 'from PyEEL import Node' instead.",
    DeprecationWarning, stacklevel=2,
)
from .Core.Node import Node  # noqa: F401, E402
__all__ = ["Node"]
