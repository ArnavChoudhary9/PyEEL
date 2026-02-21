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

from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.Components import Inductor, Resistor
from PyEEL.Components.MutualCoupling import MutualCoupling
from PyEEL.Components.Sources.VoltageSource import ACVoltageSource
from PyEEL.Probe import VoltageProbe, CurrentProbe

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

# Secondary loop: GND → L2 → n3 → R_load → GND  (closed via ground)
L2 = Inductor("L2", (gnd, n3), inductance=10e-3)
ckt.AddComponent(L2)
ckt.AddComponent(Resistor("R_load", (n3, gnd), resistance=10.0))

# Mutual coupling (k = 0.8)
K1 = MutualCoupling("K1", L1, L2, k=0.8)
ckt.AddComponent(K1)

# ── probes ──────────────────────────────────────────────────────────
v_n1 = VoltageProbe("V(n1)", n1)
v_n2 = VoltageProbe("V(n2)", n2)
v_n3 = VoltageProbe("V(n3) secondary", n3)
i_L1 = CurrentProbe("I(L1)", L1)
i_L2 = CurrentProbe("I(L2)", L2)

ckt.AddProbe(v_n1)
ckt.AddProbe(v_n2)
ckt.AddProbe(v_n3)
ckt.AddProbe(i_L1)
ckt.AddProbe(i_L2)

ckt.Finalize()

# ── simulate ────────────────────────────────────────────────────────
dt     = 1e-4          # 100 µs
t_end  = 0.06          # 3 full cycles at 50 Hz
steps  = int(t_end / dt)

print(f"M = {K1.MutualInductance*1e3:.2f} mH   (k = {K1.CouplingCoefficient})")
print(f"Simulating {steps} steps  (dt = {dt*1e6:.0f} µs, t_end = {t_end*1e3:.0f} ms)\n")

for _ in range(steps):
    x = ckt.Simulate(dt)

# ── report ──────────────────────────────────────────────────────────
print(f"{'Time (ms)':>10}  {'V(n1)':>8}  {'V(n3)':>8}  {'I(L1)':>8}  {'I(L2)':>8}")
print("-" * 54)

# Print last 10 data points
times  = v_n1.TimeData[-10:]
vn1    = v_n1.ValueData[-10:]
vn3    = v_n3.ValueData[-10:]
iL1    = i_L1.ValueData[-10:]
iL2    = i_L2.ValueData[-10:]

for t, v1, v3, i1, i2 in zip(times, vn1, vn3, iL1, iL2):
    print(f"{t*1e3:10.3f}  {v1:8.4f}  {v3:8.4f}  {i1:8.4f}  {i2:8.4f}")

# Quick sanity check: secondary should have non-zero current
peak_i2 = max(abs(v) for v in i_L2.ValueData[len(i_L2.ValueData)//2:])
assert peak_i2 > 0.01, (
    f"Secondary current too small ({peak_i2:.6f} A) — coupling may not be working!"
)
print(f"\n✓  Peak |I(L2)| in second half = {peak_i2:.4f} A  (coupling is active)")
