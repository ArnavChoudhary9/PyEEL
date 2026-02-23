"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.LivePlotter' is deprecated. Use 'from PyEEL import LivePlotter' instead.",
    DeprecationWarning, stacklevel=2,
)
from .Visualization.LivePlotter import LivePlotter  # noqa: F401, E402
__all__ = ["LivePlotter"]
