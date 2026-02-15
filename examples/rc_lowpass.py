"""
RC Low-Pass Filter
===================
V1 (AC 5 V, 100 Hz) ──(n1)── R1 1 kΩ ──(n2)── C1 1 μF ──(GND)

Cutoff frequency  f_c = 1/(2π·R·C) ≈ 159 Hz
At 100 Hz the signal passes with mild attenuation.
Above 159 Hz, the output at n2 rolls off at -20 dB/decade.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.Components import Resistor, Capacitor
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
ckt.AddComponent(Resistor("R1", (n1, n2), resistance=1000.0))
ckt.AddComponent(Capacitor("C1", (n2, gnd), capacitance=1e-6))

# ── probes ──────────────────────────────────────────────────────────
v_in  = VoltageProbe("V_in",  n1)
v_out = VoltageProbe("V_out", n2)
i_r   = CurrentProbe("I(R1)", ckt._Components[1])

ckt.AddProbe(v_in)
ckt.AddProbe(v_out)
ckt.AddProbe(i_r)
ckt.Finalize()

# ── schematic ───────────────────────────────────────────────────────
drawer = SchematicDrawer.FromCircuit(ckt)
drawer.Summary()
drawer.Save("examples/rc_lowpass.png")
drawer.Draw()

# ── simulation ──────────────────────────────────────────────────────
plotter = LivePlotter(
    [v_in, v_out],
    [i_r],
    window=0.05,
)
sim = LiveSimulation(ckt, plotter, dt=0.00005, speed=60)
sim.Run()
