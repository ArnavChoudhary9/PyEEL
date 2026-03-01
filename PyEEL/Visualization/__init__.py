"""
Visualization sub-package — probes, live plotting, scope, and static plots.
"""

from .Probe import Probe, ProbeType, VoltageProbe, CurrentProbe
from .PlotterProtocol import LivePlotterProtocol
from .LivePlotter import LivePlotter
from .LiveSimulation import LiveSimulation
from .Plotting import (
    plot_bode,
    plot_noise_spectrum,
    plot_monte_carlo,
    plot_sweep,
    plot_harmonic_spectrum,
    plot_transient,
)

# Scope — oscilloscope-style replacement for LivePlotter
from .Scope import (
    Scope,
    ScopeChannel,
    ScopeRenderer,
    CircularBuffer,
    Trigger,
    TriggerEdge,
    TriggerMode,
    TriggerState,
    compute_measurements,
    MeasurementResult,
)

__all__ = [
    "Probe",
    "ProbeType",
    "VoltageProbe",
    "CurrentProbe",
    "LivePlotterProtocol",
    "LivePlotter",
    "LiveSimulation",
    # Scope (oscilloscope)
    "Scope",
    "ScopeChannel",
    "ScopeRenderer",
    "CircularBuffer",
    "Trigger",
    "TriggerEdge",
    "TriggerMode",
    "TriggerState",
    "compute_measurements",
    "MeasurementResult",
    # Static analysis plots
    "plot_bode",
    "plot_noise_spectrum",
    "plot_monte_carlo",
    "plot_sweep",
    "plot_harmonic_spectrum",
    "plot_transient",
]
