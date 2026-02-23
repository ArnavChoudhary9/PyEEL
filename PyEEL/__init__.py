"""
PyEEL — Python Electronics Engineering Library.

All public symbols are re-exported here for convenience so that
``from PyEEL import *`` and ``from PyEEL.XYZ import ABC`` both work.
"""

# ── Core ────────────────────────────────────────────────────────────
from .Core import (
    Node, NodeManager, GROUND_NODE_NAME,
    SimulationMode, IntegrationMethod, SimulationConfig, SimulationContext,
)

# ── Components ──────────────────────────────────────────────────────
from .Components.Component import Component
from .Components.Passive import Resistor, Capacitor, Inductor
from .Components.Semiconductors import (
    Diode, ZenerDiode, BJT, BJTType, NPN, PNP, MOSFET, MOSFETType, NMOS, PMOS,
)
from .Components.Magnetic import MutualCoupling, Transformer
from .Components.ICs import OpAmp, Comparator
from .Components.Sources import (
    Source, VoltageSource, ACVoltageSource, DCVoltageSource,
    VCVS, VCCS, CCVS, CCCS,
    Waveform, ConstantWave, SineWave,
)

# ── Solver ──────────────────────────────────────────────────────────
from .Solver import (
    LinearSolver, NumpySolver,
    ACAnalysis, ACResult,
    NoiseAnalysis, NoiseResult,
    HarmonicBalance, HBResult,
)

# ── Simulation ──────────────────────────────────────────────────────
from .Simulation import (
    Circuit,
    EventDetector, EventRecord,
    ZeroCrossing, ThresholdCrossing, CustomEvent, CrossingDirection,
    MonteCarlo, Tolerance, MonteCarloResult,
    ParameterSweep, SweepResult,
)

# ── Visualization ───────────────────────────────────────────────────
from .Visualization import (
    Probe, ProbeType, VoltageProbe, CurrentProbe,
    LivePlotter, LiveSimulation,
    plot_bode, plot_noise_spectrum, plot_monte_carlo,
    plot_sweep, plot_harmonic_spectrum, plot_transient,
)

# ── Common building blocks ──────────────────────────────────────────
from .Components import common

# ── Pre-built component library (real-world parts) ─────────────────
from .Components import library
