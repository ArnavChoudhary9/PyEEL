"""
PyEEL – main test / demo script
================================
Demonstrates live plotting with multiple probes displayed simultaneously.
"""

from PyEEL import *
from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.Components import Resistor
from PyEEL.Components.Sources.VoltageSource import (
    DCVoltageSource, ACVoltageSource,
)
from PyEEL.Probe import VoltageProbe, CurrentProbe
from PyEEL.LivePlotter import LivePlotter

# ── build circuit: AC source → voltage divider ─────────────────────
ckt = Circuit(solver=NumpySolver())

nm  = ckt.NodeManager
gnd = nm.GroundNode
n1  = nm.AddNode("n1")
n2  = nm.AddNode("n2")

ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=5.0, frequency=2.0))
ckt.AddComponent(Resistor("R1", (n1, n2), resistance=1000.0))
ckt.AddComponent(Resistor("R2", (n2, gnd), resistance=1000.0))

# ── probes ──────────────────────────────────────────────────────────
v_n1 = VoltageProbe("V(n1)", n1)
v_n2 = VoltageProbe("V(n2)", n2)
i_r1 = CurrentProbe("I(R1)", ckt._Components[1])   # R1

ckt.AddProbe(v_n1)
ckt.AddProbe(v_n2)
ckt.AddProbe(i_r1)

ckt.Finalize()

# ── live plotter ────────────────────────────────────────────────────
# Group 1 (subplot 1): both voltage probes overlaid on the same axes
# Group 2 (subplot 2): current probe on its own axes
# All update together in one window.
plotter = LivePlotter(
    [v_n1, v_n2],       # same subplot — two voltage waveforms
    [i_r1],             # separate subplot — current
    window=1.0,         # show last 2 seconds of data
)

dt = 0.01

# Run until the user closes the plot window
while plotter.IsOpen:
    ckt.Simulate(dt)
    plotter.Update()

print("Plot window closed — simulation stopped.")
