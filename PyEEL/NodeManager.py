"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.NodeManager' is deprecated. Use 'from PyEEL import NodeManager' instead.",
    DeprecationWarning, stacklevel=2,
)
from .Core.NodeManager import NodeManager, GROUND_NODE_NAME  # noqa: F401, E402
__all__ = ["NodeManager", "GROUND_NODE_NAME"]
