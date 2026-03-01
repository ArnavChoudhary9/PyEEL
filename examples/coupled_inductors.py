"""
PyEEL – Coupled Inductor (Transformer) Test
=============================================
Two inductors coupled via MutualCoupling (k = 0.8) driven by an AC source.

Topology (1:1 transformer, k = 0.8)::

    Primary:   V1 (AC 5 V, 50 Hz) ──(n1)── L1 10 mH ──(n2)── R1 10 Ω ──(GND)
    Secondary: (GND)── L2 10 mH ──(n3)── R_load 10 Ω ──(GND)

    K1 couples L1 ↔ L2 with k = 0.8
    M  = k·√(L1·L2) = 0.8·10 mH = 8 mH

The secondary winding (L2) and the load resistor (R_load) are both
referenced to ground, forming a closed loop.  Coupling induces a
voltage across L2 which appears at n3 and drives current through R_load.
"""

from PyEEL import *

# ── build circuit ───────────────────────────────────────────────────
ckt = Circuit(solver=NumpySolver())
nm  = ckt.NodeManager
gnd = nm.GroundNode
n1  = nm.AddNode("n1")
n2  = nm.AddNode("n2")
n3  = nm.AddNode("n3")

# Primary loop: V1 → n1 → L1 → n2 → R1 → GND
ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=5.0, frequency=50.0))
L1 = Inductor("L1", (n1, n2), inductance=10e-3)
ckt.AddComponent(L1)
ckt.AddComponent(Resistor("R1", (n2, gnd), resistance=10.0))

# Secondary loop: GND → L2 → n3 → R_load → GND
L2 = Inductor("L2", (gnd, n3), inductance=10e-3)
ckt.AddComponent(L2)
ckt.AddComponent(Resistor("R_load", (n3, gnd), resistance=10.0))

# Mutual coupling (k = 0.8)
K1 = MutualCoupling("K1", L1, L2, k=0.8)
ckt.AddComponent(K1)

# ── probes ──────────────────────────────────────────────────────────
v_n1 = VoltageProbe("V(n1)", n1)
v_n3 = VoltageProbe("V(n3) secondary", n3)
i_L1 = CurrentProbe("I(L1)", L1)
i_L2 = CurrentProbe("I(L2)", L2)

ckt.AddProbe(v_n1)
ckt.AddProbe(v_n3)
ckt.AddProbe(i_L1)
ckt.AddProbe(i_L2)

ckt.Finalize()

print(f"M = {K1.MutualInductance*1e3:.2f} mH   (k = {K1.CouplingCoefficient})")

# ── scope ───────────────────────────────────────────────────────────
scope = Scope(
    [v_n1, v_n3],
    [i_L1, i_L2],
    window=0.06,
    title="Coupled Inductors (k=0.8)",
)

sim = LiveSimulation(ckt, scope, dt=1e-4, speed=60)
sim.Run()
