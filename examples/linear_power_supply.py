"""
PyEEL — Linear Power Supply Demo
===================================
Models a 240 V AC mains supply stepped down to ~12 V AC by a
transformer, then full-bridge rectified and filtered.

Topology::

    ┌───────────────── TRANSFORMER ──────────────────┐
    │  Primary (240 Vrms, 50 Hz)   Secondary (~12 V) │
    │  p1 ──┤ L1 ├── p2           s1 ──┤ L2 ├── s2  │
    └────────────────────────────────────────────────-┘

              Full-Bridge Rectifier
              ~~~~~~~~~~~~~~~~~~~~~~
               s1 ──┬── D1 →──┬── dc+
                    │         │
                    └── D3 ←──┘
                              │
               s2 ──┬── D2 →──┤
                    │         │
                    └── D4 ←──┘── dc-  (GND)

    dc+ ──┤ C1 (filter) ├── GND
    dc+ ──┤ R_load       ├── GND

Design notes
------------
  • Primary inductance   L1 = 10 H   (realistic mains-frequency core)
  • Turns ratio          n  = 20:1   → secondary voltage ≈ 12 V peak
  • Secondary inductance L2 = L1/n²  = 0.025 H
  • Coupling coefficient k  = 0.999  (close to ideal)
  • Filter capacitor     C1 = 1000 µF
  • Load resistor        R  = 100 Ω  → ≈120 mA load

Probes:
  • V(p1)  — primary (mains) voltage
  • V(s1)  — secondary voltage
  • V(dc+) — rectified + filtered DC output
"""

from PyEEL import *

# ── configuration ───────────────────────────────────────────────────
config = SimulationConfig(
    dc_operating_point=True,
    gmin=1e-12,
    nr_max_iterations=100,          # more headroom for 7-diode-drop bridge
    nr_abs_tolerance=1e-6,
    source_stepping_steps=20,       # gentle ramp for large-signal startup
)

# ── build circuit ───────────────────────────────────────────────────
ckt = Circuit(solver=NumpySolver(), config=config)

nm  = ckt.NodeManager
gnd = nm.GroundNode          # dc- / neutral reference

# Transformer nodes
p1 = nm.AddNode("p1")       # primary +
p2 = nm.AddNode("p2")       # primary - (can float or tie to gnd)
s1 = nm.AddNode("s1")       # secondary +
s2 = nm.AddNode("s2")       # secondary -

# DC output node
dc_plus = nm.AddNode("dc+")

# ── 1. AC mains source (240 Vrms → peak ≈ 339.4 V) ────────────────
import math
V_rms = 240.0
V_peak = V_rms * math.sqrt(2)
ckt.AddComponent(ACVoltageSource(
    "V_mains", (p1, p2), amplitude=V_peak, frequency=50.0,
))

# ── 2. Step-down transformer (20:1 turns ratio) ────────────────────
n_ratio = 20.0
L_primary = 10.0                           # 10 H
L_secondary = L_primary / (n_ratio ** 2)   # 0.025 H
k = 0.999

ckt.AddComponent(Transformer(
    "T1",
    primary_nodes=(p1, p2),
    secondary_nodes=(s1, s2),
    primary_inductance=L_primary,
    secondary_inductance=L_secondary,
    k=k,
))

# ── 3. Full-bridge rectifier (4 diodes) ────────────────────────────
#
#   s1 ──→ D1 ──→ dc+      (positive half-cycle path)
#   gnd ←─ D3 ←── s1       (return path, negative rail)
#   s2 ──→ D2 ──→ dc+      (negative half-cycle path)
#   gnd ←─ D4 ←── s2       (return path, negative rail)
#
# Using 1N4007-ish parameters for power diodes
diode_params = dict(Is=1e-10, n=1.8)

ckt.AddComponent(Diode("D1", (s1, dc_plus), **diode_params))   # s1 → dc+
ckt.AddComponent(Diode("D2", (s2, dc_plus), **diode_params))   # s2 → dc+
ckt.AddComponent(Diode("D3", (gnd, s1),     **diode_params))   # gnd → s1
ckt.AddComponent(Diode("D4", (gnd, s2),     **diode_params))   # gnd → s2

# ── 4. Filter capacitor ────────────────────────────────────────────
ckt.AddComponent(Capacitor("C1", (dc_plus, gnd), capacitance=1000e-6))

# ── 5. Load resistor ───────────────────────────────────────────────
ckt.AddComponent(Resistor("R_load", (dc_plus, gnd), resistance=100.0))

# ── 6. Tie primary return to ground through small R (avoids float) ──
ckt.AddComponent(Resistor("R_gnd", (p2, gnd), resistance=0.01))

# ── probes ──────────────────────────────────────────────────────────
v_mains = VoltageProbe("V(mains)", p1)      # primary voltage
v_sec   = VoltageProbe("V(sec)",   s1)      # secondary voltage
v_dc    = VoltageProbe("V(dc+)",   dc_plus) # DC output

ckt.AddProbe(v_mains)
ckt.AddProbe(v_sec)
ckt.AddProbe(v_dc)

# ── simulate ────────────────────────────────────────────────────────
ckt.Finalize()

scope = Scope(
    [v_sec, v_dc],
    [v_mains],
    window=100e-3,
    title="Linear Power Supply",
)

sim = LiveSimulation(
    ckt, scope,
    dt=2e-5,
    speed=200,
)

sim.Run()
