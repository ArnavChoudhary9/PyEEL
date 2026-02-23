"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.Probe' is deprecated. Use 'from PyEEL import Probe' instead.",
    DeprecationWarning, stacklevel=2,
)
from .Visualization.Probe import Probe, ProbeType, VoltageProbe, CurrentProbe  # noqa: F401, E402
__all__ = ["Probe", "ProbeType", "VoltageProbe", "CurrentProbe"]
