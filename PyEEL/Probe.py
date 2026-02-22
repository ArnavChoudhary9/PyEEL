"""Backward-compatibility shim. Import from ``PyEEL.Visualization.Probe`` instead."""
from .Visualization.Probe import Probe, ProbeType, VoltageProbe, CurrentProbe
__all__ = ["Probe", "ProbeType", "VoltageProbe", "CurrentProbe"]
