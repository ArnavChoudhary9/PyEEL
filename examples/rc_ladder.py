"""
RC Ladder Network (3-stage)
============================
V1 (AC 5 V, 100 Hz) ──(n1)── R1 ──(n2)── R2 ──(n3)── R3 ──(n4)
                                │           │           │
                               C1          C2          C3
                                │           │           │
                              (GND) ───── (GND) ───── (GND)

Each RC section attenuates and phase-shifts the signal.
Three cascaded sections create a cumulative low-pass response.

Component values:  R = 1 kΩ,  C = 100 nF
Per-section cutoff  f_c = 1/(2π·RC) ≈ 1592 Hz
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.Components import Resistor, Capacitor
from PyEEL.Components.Sources.VoltageSource import ACVoltageSource
from PyEEL.Probe import VoltageProbe
from PyEEL.LivePlotter import LivePlotter
from PyEEL.LiveSimulation import LiveSimulation
from PyEEL.SchematicDrawer import SchematicDrawer

# ── circuit ─────────────────────────────────────────────────────────
ckt = Circuit(solver=NumpySolver())
nm  = ckt.NodeManager
gnd = nm.GroundNode
n1  = nm.AddNode("n1")
n2  = nm.AddNode("n2")
n3  = nm.AddNode("n3")
n4  = nm.AddNode("n4")

R = 1000.0      # 1 kΩ
C = 100e-9      # 100 nF

ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=5.0, frequency=100.0))
ckt.AddComponent(Resistor("R1", (n1, n2), resistance=R))
ckt.AddComponent(Capacitor("C1", (n2, gnd), capacitance=C))
ckt.AddComponent(Resistor("R2", (n2, n3), resistance=R))
ckt.AddComponent(Capacitor("C2", (n3, gnd), capacitance=C))
ckt.AddComponent(Resistor("R3", (n3, n4), resistance=R))
ckt.AddComponent(Capacitor("C3", (n4, gnd), capacitance=C))

# ── probes (voltage at each stage) ──────────────────────────────────
v1 = VoltageProbe("V(n1)", n1)   # input
v2 = VoltageProbe("V(n2)", n2)   # after stage 1
v3 = VoltageProbe("V(n3)", n3)   # after stage 2
v4 = VoltageProbe("V(n4)", n4)   # after stage 3 (output)

ckt.AddProbe(v1)
ckt.AddProbe(v2)
ckt.AddProbe(v3)
ckt.AddProbe(v4)
ckt.Finalize()

# ── schematic ───────────────────────────────────────────────────────
drawer = SchematicDrawer.FromCircuit(ckt)
drawer.Summary()
drawer.Save("examples/rc_ladder.png")
drawer.Draw()

# ── simulation ──────────────────────────────────────────────────────
plotter = LivePlotter(
    [v1, v2, v3, v4],
    window=0.05,
)
sim = LiveSimulation(ckt, plotter, dt=0.00005, speed=60)
sim.Run()
