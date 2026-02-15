"""
Voltage Divider
================
V1 (AC 10 V, 50 Hz) ──(n1)── R1 1 kΩ ──(n2)── R2 1 kΩ ──(GND)

Output voltage at n2:  V_out = V_in × R2/(R1+R2) = V_in × 0.5
With equal resistors the output is exactly half the input.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.Components import Resistor
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

ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=10.0, frequency=50.0))
ckt.AddComponent(Resistor("R1", (n1, n2), resistance=1000.0))
ckt.AddComponent(Resistor("R2", (n2, gnd), resistance=1000.0))

# ── probes ──────────────────────────────────────────────────────────
v_in  = VoltageProbe("V_in",  n1)
v_out = VoltageProbe("V_out", n2)
i_r1  = CurrentProbe("I(R1)", ckt._Components[1])

ckt.AddProbe(v_in)
ckt.AddProbe(v_out)
ckt.AddProbe(i_r1)
ckt.Finalize()

# ── schematic ───────────────────────────────────────────────────────
drawer = SchematicDrawer.FromCircuit(ckt)
drawer.Summary()
drawer.Save("examples/voltage_divider.png")
drawer.Draw()

# ── simulation ──────────────────────────────────────────────────────
plotter = LivePlotter(
    [v_in, v_out],
    [i_r1],
    window=0.1,
)
sim = LiveSimulation(ckt, plotter, dt=0.0001, speed=60)
sim.Run()
