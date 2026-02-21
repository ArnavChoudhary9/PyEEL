"""
Series LCR Circuit
===================
V1 (AC 5 V, 5 Hz) ──(n1)── L1 0.1 H ──(n2)── C1 10 mF ──(n3)── R1 1 Ω ──(GND)

Resonant frequency  f₀ = 1/(2π√LC) ≈ 5.03 Hz  (≈ drive frequency)
Quality factor       Q  = (1/R)·√(L/C) ≈ 3.16

At resonance the impedance of L and C cancel, leaving only R.
The current and voltage across R peak sharply.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.Components import Resistor, Capacitor, Inductor
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
n3  = nm.AddNode("n3")

ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=5.0, frequency=5.0))
ckt.AddComponent(Inductor("L1", (n1, n2), inductance=0.1))
ckt.AddComponent(Capacitor("C1", (n2, n3), capacitance=0.01))
ckt.AddComponent(Resistor("R1", (n3, gnd), resistance=1.0))

# ── probes ──────────────────────────────────────────────────────────
v_src = VoltageProbe("V(n1)", n1)
v_cap = VoltageProbe("V(n2)", n2)
v_res = VoltageProbe("V(n3)", n3)
i_l   = CurrentProbe("I(L1)", ckt._Components[1])

ckt.AddProbe(v_src)
ckt.AddProbe(v_cap)
ckt.AddProbe(v_res)
ckt.AddProbe(i_l)
ckt.Finalize()

# ── schematic ───────────────────────────────────────────────────────
drawer = SchematicDrawer.FromCircuit(ckt)
drawer.Summary()
drawer.Save("examples/series_lcr.png")
drawer.Draw()

# ── simulation ──────────────────────────────────────────────────────
plotter = LivePlotter(
    [v_src, v_cap, v_res],
    [i_l],
    window=1.0,
)
sim = LiveSimulation(ckt, plotter, dt=0.0005, speed=60)
sim.Run()
