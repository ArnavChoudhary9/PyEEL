"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.Components.MutualCoupling' is deprecated. Use 'from PyEEL import MutualCoupling' instead.",
    DeprecationWarning, stacklevel=2,
)
from .Magnetic.MutualCoupling import MutualCoupling  # noqa: F401, E402
__all__ = ["MutualCoupling"]
