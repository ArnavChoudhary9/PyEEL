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

# ── build circuit ───────────────────────────────────────────────────
ckt = Circuit(solver=NumpySolver())

nm  = ckt.NodeManager
gnd = nm.GroundNode
n1  = nm.AddNode("n1")
n2  = nm.AddNode("n2")
n3  = nm.AddNode("n3")

#  V1 ──(n1)── L1 ──(n2)── C1 ──(n3)── R1 ──(gnd)
ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=5.0, frequency=5.0))
ckt.AddComponent(l := Inductor("L1", (n1, n2), inductance=0.1))
ckt.AddComponent(Capacitor("C1", (n2, n3), capacitance=0.01))
ckt.AddComponent(Resistor("R1", (n3, gnd), resistance=1.0))

# ── probes ──────────────────────────────────────────────────────────
v_n1 = VoltageProbe("V(n1)", n1)            # source voltage
v_n2 = VoltageProbe("V(n2)", n2)            # after inductor
v_n3 = VoltageProbe("V(n3)", n3)            # across R (= V_R)
i_l1 = CurrentProbe("I(L1)", l)             # series current

ckt.AddProbe(v_n1)
ckt.AddProbe(v_n2)
ckt.AddProbe(v_n3)
ckt.AddProbe(i_l1)

ckt.Finalize()

# ── scope ───────────────────────────────────────────────────────────
scope = Scope(
    [v_n1, v_n2, v_n3],     # CH1-3 — voltages
    [i_l1],                 # CH4   — current
    window=1.0,
    title="LCR Series Circuit",
)

# ── run ─────────────────────────────────────────────────────────────
sim = LiveSimulation(ckt, scope, dt=0.0005, speed=60)
sim.Run()
