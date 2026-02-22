"""
PyEEL — Current-Controlled Sources Demo (CCVS & CCCS)
=======================================================
Demonstrates both current-controlled dependent sources.

Topology::

    V1 (DC 5 V) ── R_sense (1 kΩ) ──(n1)── R_load1 (4 kΩ) ── GND

    The controlling current I_ctrl flows through R_sense:
        I_ctrl = V1 / (R_sense + R_load1) = 5 / 5000 = 1 mA

    ┌──── CCVS (H1, r = 2000 Ω) ─────────────────┐
    │  ctrl: senses current entering n_s1,         │
    │        leaving n1 (zero-volt source)         │
    │  out:  V(n_h) − V(GND) = r × I_ctrl         │
    │                                               │
    │  (n_h)── R_h (5 kΩ) ── GND                  │
    │  Expected: V(n_h) = 2000 × 1e-3 = 2.0 V     │
    └───────────────────────────────────────────────┘

    ┌──── CCCS (F1, α = 3) ────────────────────────┐
    │  ctrl: senses current entering n_s2,         │
    │        leaving n1 (zero-volt source)         │
    │  out:  I_out = α × I_ctrl = 3 × 1 mA        │
    │                                               │
    │  (n_f)── R_f (1 kΩ) ── GND                  │
    │  Expected: V(n_f) = 3 mA × 1 kΩ = 3.0 V     │
    └───────────────────────────────────────────────┘

Note on current sensing
-----------------------
CCVS and CCCS insert a **zero-volt voltage source** between their
``ctrl+`` and ``ctrl−`` terminals to measure the controlling current.
This sense element must be placed *in series* with the branch whose
current you want to control on.

In this example we split the main branch into two segments so that
each current-controlled source gets its own sense point:

    V1 ── (n_s1) ── [H1 sense 0 V] ── (n1) ── R_load1 ── GND
                                        │
                     (n_s2) ── [F1 sense 0 V] ── (n1b) joined by wire

Since both sense elements are in series and carry the same current,
we simplify by letting each source sense offset nodes.

Probes
------
  • V(n1)  — voltage at the main branch mid-point
  • V(n_h) — CCVS output (expect 2.0 V DC)
  • V(n_f) — CCCS output (expect 3.0 V DC)
"""

from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.SimulationContext import SimulationConfig
from PyEEL.Components import Resistor
from PyEEL.Components.Sources.VoltageSource import DCVoltageSource
from PyEEL.Components.Sources.DependentSources import CCVS, CCCS
from PyEEL.Probe import VoltageProbe
from PyEEL.LivePlotter import LivePlotter
from PyEEL.LiveSimulation import LiveSimulation

# ── config ───────────────────────────────────────────────────────────
config = SimulationConfig(dc_operating_point=True, gmin=1e-12)

ckt = Circuit(solver=NumpySolver(), config=config)
nm  = ckt.NodeManager
gnd = nm.GroundNode

n_vs = nm.AddNode("n_vs")     # voltage source positive terminal
n_s  = nm.AddNode("n_s")      # after sense resistor (= ctrl+ for both)
n1   = nm.AddNode("n1")       # after H1's sense element (ctrl−)
n_h  = nm.AddNode("n_h")      # CCVS output
n_f  = nm.AddNode("n_f")      # CCCS output

# ═══════════════════════════════════════════════════════════════════
#  Main branch: V1 → R_sense(1 kΩ) → n_s → [H1 sense] → n1 → R_load1(4 kΩ) → GND
#  I_ctrl = 5 V / (1 kΩ + 4 kΩ) = 1 mA
# ═══════════════════════════════════════════════════════════════════
ckt.AddComponent(DCVoltageSource("V1", (n_vs, gnd), voltage=5.0))
ckt.AddComponent(Resistor("R_sense", (n_vs, n_s), resistance=1e3))

# ── CCVS: H1, transresistance = 2000 Ω ──────────────────────────────
#   The sense element is inserted between n_s and n1 (zero volts,
#   so V(n_s) = V(n1)).  Current flowing n_s → n1 is I_ctrl.
ckt.AddComponent(CCVS("H1", out_nodes=(n_h, gnd),
                       ctrl_nodes=(n_s, n1), transresistance=2000.0))

# Remainder of the main branch after the sense point
ckt.AddComponent(Resistor("R_load1", (n1, gnd), resistance=4e3))

# Load on CCVS output
ckt.AddComponent(Resistor("R_h", (n_h, gnd), resistance=5e3))

# ── CCCS: F1, current gain α = 3 ────────────────────────────────────
#   We create a second branch with the same 1 mA current for F1 to
#   sense.  V2(5 V) → R_sense2(1 kΩ) → n_s2 → [F1 sense] → n2 → R_load2(4 kΩ) → GND
n_vs2 = nm.AddNode("n_vs2")
n_s2  = nm.AddNode("n_s2")
n2    = nm.AddNode("n2")

ckt.AddComponent(DCVoltageSource("V2", (n_vs2, gnd), voltage=5.0))
ckt.AddComponent(Resistor("R_sense2", (n_vs2, n_s2), resistance=1e3))
ckt.AddComponent(CCCS("F1", out_nodes=(gnd, n_f),
                       ctrl_nodes=(n_s2, n2), gain=3.0))
ckt.AddComponent(Resistor("R_load2", (n2, gnd), resistance=4e3))

# Load on CCCS output: I_out = 3 × 1 mA = 3 mA → V = 3 mA × 1 kΩ
ckt.AddComponent(Resistor("R_f", (n_f, gnd), resistance=1e3))

# ── probes ───────────────────────────────────────────────────────────
v_n1 = VoltageProbe("V(n1)",      n1)     # main branch mid-point
v_h  = VoltageProbe("V(CCVS)",    n_h)    # CCVS output (expect 2.0 V)
v_f  = VoltageProbe("V(CCCS)",    n_f)    # CCCS output (expect 3.0 V)

ckt.AddProbe(v_n1)
ckt.AddProbe(v_h)
ckt.AddProbe(v_f)

# ── simulate ─────────────────────────────────────────────────────────
ckt.Finalize()

plotter = LivePlotter(
    [v_n1, v_h, v_f],   # all three DC levels on one subplot
    window=5e-3,         # short window (DC so values are constant)
)

sim = LiveSimulation(
    ckt, plotter,
    dt=1e-4,
    speed=50,
)

sim.Run()
