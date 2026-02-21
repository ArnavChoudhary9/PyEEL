"""
Wheatstone Bridge
==================

         ┌── R1 1 kΩ ──(n2)── R2 2 kΩ ──┐
  V1 ──(n1)                              (GND)
         └── R3 1 kΩ ──(n3)── R4 2 kΩ ──┘

                      Rg 500 Ω
                  (n2) ──── (n3)

Bridge balance condition: R1/R2 = R3/R4
Here R1/R2 = R3/R4 = 0.5 → bridge is balanced → V(n2)-V(n3) ≈ 0.

The galvanometer Rg connects the two midpoints.
At balance, no current flows through Rg.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.Components import Resistor
from PyEEL.Components.Sources.VoltageSource import DCVoltageSource
from PyEEL.Probe import VoltageProbe, CurrentProbe
from PyEEL.LivePlotter import LivePlotter
from PyEEL.LiveSimulation import LiveSimulation
from PyEEL.SchematicDrawer import SchematicDrawer

# ── circuit ─────────────────────────────────────────────────────────
ckt = Circuit(solver=NumpySolver())
nm  = ckt.NodeManager
gnd = nm.GroundNode
n1  = nm.AddNode("n1")      # source terminal
n2  = nm.AddNode("n2")      # top midpoint
n3  = nm.AddNode("n3")      # bottom midpoint

ckt.AddComponent(DCVoltageSource("V1", (n1, gnd), voltage=10.0))
ckt.AddComponent(Resistor("R1", (n1, n2), resistance=1000.0))   # top-left arm
ckt.AddComponent(Resistor("R2", (n2, gnd), resistance=2000.0))  # top-right arm
ckt.AddComponent(Resistor("R3", (n1, n3), resistance=1000.0))   # bottom-left arm
ckt.AddComponent(Resistor("R4", (n3, gnd), resistance=2000.0))  # bottom-right arm
ckt.AddComponent(Resistor("Rg", (n2, n3), resistance=500.0))    # galvanometer

# ── probes ──────────────────────────────────────────────────────────
v_n1    = VoltageProbe("V(n1)",   n1)
v_n2    = VoltageProbe("V(n2)",   n2)
v_n3    = VoltageProbe("V(n3)",   n3)
v_bridge = VoltageProbe("V_bridge", n2, n3)      # differential
i_rg    = CurrentProbe("I(Rg)",   ckt._Components[5])

ckt.AddProbe(v_n1)
ckt.AddProbe(v_n2)
ckt.AddProbe(v_n3)
ckt.AddProbe(v_bridge)
ckt.AddProbe(i_rg)
ckt.Finalize()

# ── schematic ───────────────────────────────────────────────────────
drawer = SchematicDrawer.FromCircuit(ckt)
drawer.Summary()
drawer.Save("examples/wheatstone.png")
drawer.Draw()

# ── simulation ──────────────────────────────────────────────────────
plotter = LivePlotter(
    [v_n2, v_n3, v_bridge],
    [i_rg],
    window=0.5,
)
sim = LiveSimulation(ckt, plotter, dt=0.001, speed=60)
sim.Run()
