"""
Parallel RC Circuit
====================
V1 (AC 5 V, 50 Hz) ──(n1)── R1 1 kΩ ──(GND)
                       │                  │
                       └── C1 10 μF ──────┘

R and C are in parallel between n1 and GND.

At low frequencies C is an open circuit → all current through R.
At high frequencies C is a short circuit → current bypasses R.
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

ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=5.0, frequency=50.0))
ckt.AddComponent(Resistor("R1", (n1, gnd), resistance=1000.0))
ckt.AddComponent(Capacitor("C1", (n1, gnd), capacitance=10e-6))

# ── probes ──────────────────────────────────────────────────────────
v_n1 = VoltageProbe("V(n1)", n1)
i_r  = CurrentProbe("I(R1)", ckt._Components[1])
i_c  = CurrentProbe("I(C1)", ckt._Components[2])

ckt.AddProbe(v_n1)
ckt.AddProbe(i_r)
ckt.AddProbe(i_c)
ckt.Finalize()

# ── schematic ───────────────────────────────────────────────────────
drawer = SchematicDrawer.FromCircuit(ckt)
drawer.Summary()
drawer.Save("examples/parallel_rc.png")
drawer.Draw()

# ── simulation ──────────────────────────────────────────────────────
plotter = LivePlotter(
    [v_n1],
    [i_r, i_c],
    window=0.1,
)
sim = LiveSimulation(ckt, plotter, dt=0.0001, speed=60)
sim.Run()
