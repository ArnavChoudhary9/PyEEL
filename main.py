"""
PyEEL - Series LCR Circuit Demo
=================================
Demonstrates a series LCR circuit driven by an AC source.

Topology::

    V1 (AC 5 V, 5 Hz)
     ├──(n1)── L1 0.1 H ──(n2)── C1 0.01 F ──(n3)── R1 1 Ω ──(GND)

Resonant frequency  f₀ = 1/(2π√LC) ≈ 5.03 Hz  (≈ drive frequency)
Quality factor       Q  = (1/R)·√(L/C) ≈ 3.16

Probes:
  • V(n1)  — source voltage
  • V(n2)  — voltage after inductor (across C + R)
  • V(n3)  — voltage across resistor
  • I(L1)  — series current (same everywhere in the loop)
"""

from PyEEL import *
from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.Components import Resistor, Capacitor, Inductor
from PyEEL.Components.Sources.VoltageSource import ACVoltageSource
from PyEEL.Probe import VoltageProbe, CurrentProbe
from PyEEL.LivePlotter import LivePlotter
from PyEEL.LiveSimulation import LiveSimulation
from PyEEL.SchematicDrawer import SchematicDrawer

# ── build circuit ───────────────────────────────────────────────────
ckt = Circuit(solver=NumpySolver())

nm  = ckt.NodeManager
gnd = nm.GroundNode
n1  = nm.AddNode("n1")
n2  = nm.AddNode("n2")
n3  = nm.AddNode("n3")

#  V1 ──(n1)── L1 ──(n2)── C1 ──(n3)── R1 ──(gnd)
ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=5.0, frequency=5.0))
ckt.AddComponent(Inductor("L1", (n1, n2), inductance=0.1))
ckt.AddComponent(Capacitor("C1", (n2, n3), capacitance=0.01))
ckt.AddComponent(Resistor("R1", (n3, gnd), resistance=1.0))

# ── probes ──────────────────────────────────────────────────────────
v_n1 = VoltageProbe("V(n1)", n1)            # source voltage
v_n2 = VoltageProbe("V(n2)", n2)            # after inductor
v_n3 = VoltageProbe("V(n3)", n3)            # across R (= V_R)
i_l1 = CurrentProbe("I(L1)", ckt._Components[1])   # series current
i_r1 = CurrentProbe("I(R1)", ckt._Components[3])   # current through R

ckt.AddProbe(v_n1)
ckt.AddProbe(v_n2)
ckt.AddProbe(v_n3)
ckt.AddProbe(i_l1)
ckt.AddProbe(i_r1)

ckt.Finalize()

# ── schematic ───────────────────────────────────────────────────────
# Render the circuit topology as a schemdraw diagram.
drawer = SchematicDrawer.FromCircuit(ckt)
drawer.Summary()
drawer.Save("schematic.png")
drawer.Draw()                  # close the window to start simulation

# ── live plotter ────────────────────────────────────────────────────
# Subplot 1: voltages at each node overlaid
# Subplot 2: currents through L and R overlaid
plotter = LivePlotter(
    [v_n1, v_n2, v_n3],     # subplot 1 — voltages
    [i_l1, i_r1],           # subplot 2 — currents
    window=1.0,             # show the last 1 second of data
)

# ── run ─────────────────────────────────────────────────────────────
# Press Space on the plot window to pause / resume.
sim = LiveSimulation(ckt, plotter, dt=0.0005, speed=60)
sim.Run()
