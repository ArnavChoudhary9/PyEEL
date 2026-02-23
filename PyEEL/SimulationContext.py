"""Deprecated shim — import from ``PyEEL`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.SimulationContext' is deprecated. Use 'from PyEEL import SimulationContext' instead.",
    DeprecationWarning, stacklevel=2,
)
from .Core.SimulationContext import SimulationMode, IntegrationMethod, SimulationConfig, SimulationContext  # noqa: F401, E402
__all__ = ["SimulationMode", "IntegrationMethod", "SimulationConfig", "SimulationContext"]
