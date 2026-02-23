"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.Components.Transformer' is deprecated. Use 'from PyEEL import Transformer' instead.",
    DeprecationWarning, stacklevel=2,
)
from .Magnetic.Transformer import Transformer  # noqa: F401, E402
__all__ = ["Transformer"]
