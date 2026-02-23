"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.Components.ZenerDiode' is deprecated. Use 'from PyEEL import ZenerDiode' instead.",
    DeprecationWarning, stacklevel=2,
)
from .Semiconductors.ZenerDiode import ZenerDiode  # noqa: F401, E402
__all__ = ["ZenerDiode"]
