"""
PyEEL - 240 V → 5 V Step-Down Transformer Demo
================================================
Simulates a mains-frequency (50 Hz) step-down transformer reducing
240 V AC to 5 V AC, using the Transformer component.

Turns ratio   n  = V₁ / V₂  = 240 / 5  = 48
Inductance ratio  = n²       = 2304
  → L_primary   = 2.304 H
  → L_secondary = 1 mH

Topology::

    V1 (240 V AC, 50 Hz)
     │
    (n1)─── R_primary 100 Ω ───(n2)─┐
                                     ├── T1 primary  (2.304 H)
                                    GND

                                     ┌── T1 secondary (1 mH)
    (GND)────────────────────────(n3)┘
     │
    (n3)─── R_load 5 Ω ──── GND

    k = 0.99  (tight coupling, close to ideal)

Probes:
  • V(n1)      — mains source voltage  (240 V peak)
  • V(n2)      — primary voltage across T1 winding
  • V(n3)      — secondary output voltage  (≈ 5 V peak)
  • I_primary  — primary winding current
  • I_secondary— secondary winding current
"""

from PyEEL import *

# ── transformer parameters ──────────────────────────────────────────
TURNS_RATIO   = 48          # 240 V / 5 V
L_PRIMARY     = 2.304       # H   (L1 = n² × L2)
L_SECONDARY   = 1e-3        # H   (1 mH)
K             = 0.99        # coupling coefficient (< 1)

# ── build circuit ───────────────────────────────────────────────────
ckt = Circuit(solver=NumpySolver())
nm  = ckt.NodeManager
gnd = nm.GroundNode

n1 = nm.AddNode("n1")   # mains / source positive
n2 = nm.AddNode("n2")   # primary winding positive (after R_primary)
n3 = nm.AddNode("n3")   # secondary winding output (before R_load)

# Mains source: 240 V peak, 50 Hz
#   V_rms = 240 V → peak = 240 × √2 ≈ 339 V  (use 240 V peak for simplicity)
ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=240.0, frequency=50.0))

# Primary current-limiting resistor (models winding resistance + fuse)
ckt.AddComponent(Resistor("R_primary", (n1, n2), resistance=100.0))

# Transformer: primary (n2→GND), secondary (GND→n3)
T1 = Transformer("T1",
    primary_nodes=(n2, gnd),
    secondary_nodes=(gnd, n3),
    primary_inductance=L_PRIMARY,
    secondary_inductance=L_SECONDARY,
    k=K)
ckt.AddComponent(T1)

# Secondary load resistor (models load + winding resistance)
ckt.AddComponent(Resistor("R_load", (n3, gnd), resistance=5.0))

# ── probes ──────────────────────────────────────────────────────────
v_source    = VoltageProbe("V_source 240V",   n1)
v_primary   = VoltageProbe("V_primary",       n2)
v_secondary = VoltageProbe("V_secondary 5V",  n3)

i_primary   = CurrentProbe("I_primary",   T1.Primary)
i_secondary = CurrentProbe("I_secondary", T1.Secondary)

for p in (v_source, v_primary, v_secondary, i_primary, i_secondary):
    ckt.AddProbe(p)

ckt.Finalize()

# ── live plotter ────────────────────────────────────────────────────
# Subplot 1: source vs secondary voltage (very different scales — both shown)
# Subplot 2: primary vs secondary current
plotter = LivePlotter(
    [v_source, v_primary, v_secondary],   # subplot 1 — voltages
    [i_primary, i_secondary],             # subplot 2 — currents
    window=0.06,                          # 3 cycles of 50 Hz
)

# ── run ─────────────────────────────────────────────────────────────
# dt = 100 µs → 200 samples per 50 Hz cycle (good accuracy)
# Press Space on the plot window to pause / resume.
sim = LiveSimulation(ckt, plotter, dt=1e-4, speed=20)
sim.Run()
