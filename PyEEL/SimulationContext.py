"""Backward-compatibility shim. Import from ``PyEEL.Core.SimulationContext`` instead."""
from .Core.SimulationContext import SimulationMode, IntegrationMethod, SimulationConfig, SimulationContext
__all__ = ["SimulationMode", "IntegrationMethod", "SimulationConfig", "SimulationContext"]
