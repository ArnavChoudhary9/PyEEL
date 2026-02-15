"""
RL High-Pass Filter
====================
V1 (AC 5 V, 100 Hz) ──(n1)── L1 10 mH ──(n2)── R1 100 Ω ──(GND)

Cutoff frequency  f_c = R/(2π·L) ≈ 1592 Hz
At 100 Hz the inductor blocks most of the signal.
Above the cutoff the output across R approaches the full input.

This is the dual of the RC low-pass filter.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.Components import Resistor, Inductor
from PyEEL.Components.Sources.VoltageSource import ACVoltageSource
from PyEEL.Probe import VoltageProbe, CurrentProbe
from PyEEL.LivePlotter import LivePlotter
from PyEEL.LiveSimulation import LiveSimulation
from PyEEL.SchematicDrawer import SchematicDrawer

# ── circuit ─────────────────────────────────────────────────────────
ckt = Circuit(solver=NumpySolver())
nm  = ckt.NodeManager
gnd = nm.GroundNode
n1  = nm.AddNode("n1")
n2  = nm.AddNode("n2")

ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=5.0, frequency=100.0))
ckt.AddComponent(Inductor("L1", (n1, n2), inductance=0.01))
ckt.AddComponent(Resistor("R1", (n2, gnd), resistance=100.0))

# ── probes ──────────────────────────────────────────────────────────
v_in  = VoltageProbe("V_in",  n1)
v_out = VoltageProbe("V_out", n2)
i_l   = CurrentProbe("I(L1)", ckt._Components[1])

ckt.AddProbe(v_in)
ckt.AddProbe(v_out)
ckt.AddProbe(i_l)
ckt.Finalize()

# ── schematic ───────────────────────────────────────────────────────
drawer = SchematicDrawer.FromCircuit(ckt)
drawer.Summary()
drawer.Save("examples/rl_highpass.png")
drawer.Draw()

# ── simulation ──────────────────────────────────────────────────────
plotter = LivePlotter(
    [v_in, v_out],
    [i_l],
    window=0.05,
)
sim = LiveSimulation(ckt, plotter, dt=0.00005, speed=60)
sim.Run()
