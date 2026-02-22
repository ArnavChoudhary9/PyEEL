"""
PyEEL — Voltage-Controlled Sources Demo (VCVS & VCCS)
=======================================================
Demonstrates both voltage-controlled dependent sources in one circuit.

Topology::

                     ┌──────── VCVS (E1, gain=3) ───────┐
                     │  ctrl: (n1, GND)                  │
    V1 (1 V, 100 Hz) │ out:  (n_e, GND)                  │
     │               │                                    │
    (n1)──R1 (1 kΩ)──GND    (n_e)──R_e (1 kΩ)──GND      │
                                                          │
                     ┌──────── VCCS (G1, gm=2 mS) ──────┘
                     │  ctrl: (n1, GND)
                     │  out:  (GND, n_g)  — current into n_g
                     │
                     (n_g)──R_g (2 kΩ)──GND

**VCVS (E1)** — voltage gain μ = 3
  V(n_e) = 3 × V(n1)
  With V1 = 1 V peak at 100 Hz and R1 as load:
    V(n1) = 1 V peak → V(n_e) = 3 V peak.

**VCCS (G1)** — transconductance g = 2 mS
  I_out = 2e-3 × V(n1) = 2 mA peak
  Across R_g = 2 kΩ: V(n_g) = I_out × R_g = 4 V peak.

Probes
------
  • V(n1)   — input voltage (1 V sine)
  • V(n_e)  — VCVS output (3× input)
  • V(n_g)  — VCCS output across R_g (4 V peak)
"""

from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.SimulationContext import SimulationConfig
from PyEEL.Components import Resistor
from PyEEL.Components.Sources.VoltageSource import ACVoltageSource
from PyEEL.Components.Sources.DependentSources import VCVS, VCCS
from PyEEL.Probe import VoltageProbe
from PyEEL.LivePlotter import LivePlotter
from PyEEL.LiveSimulation import LiveSimulation

# ── config ───────────────────────────────────────────────────────────
config = SimulationConfig(dc_operating_point=True, gmin=1e-12)

ckt = Circuit(solver=NumpySolver(), config=config)
nm  = ckt.NodeManager
gnd = nm.GroundNode

n1   = nm.AddNode("n1")      # input node
n_e  = nm.AddNode("n_e")     # VCVS output
n_g  = nm.AddNode("n_g")     # VCCS output

# ── input source & load ─────────────────────────────────────────────
ckt.AddComponent(ACVoltageSource("V1", (n1, gnd),
                                  amplitude=1.0, frequency=100.0))

# ── VCVS: E1, gain = 3 V/V ──────────────────────────────────────────
#   Controls on V(n1, GND); output between n_e and GND.
ckt.AddComponent(VCVS("E1", out_nodes=(n_e, gnd),
                       ctrl_nodes=(n1, gnd), gain=3.0))
# Load on VCVS output (so current can flow)
ckt.AddComponent(Resistor("R_e", (n_e, gnd), resistance=1e3))

# ── VCCS: G1, transconductance = 2 mS ───────────────────────────────
#   Controls on V(n1, GND); output current into n_g.
#   out_nodes=(gnd, n_g) so that output current enters n_g,
#   giving V(n_g) = +gm × V_ctrl × R_g  (non-inverting).
ckt.AddComponent(VCCS("G1", out_nodes=(gnd, n_g),
                       ctrl_nodes=(n1, gnd), transconductance=2e-3))
# Load converts output current to a voltage
ckt.AddComponent(Resistor("R_g", (n_g, gnd), resistance=2e3))

# ── probes ───────────────────────────────────────────────────────────
v_in = VoltageProbe("V(input)", n1)
v_e  = VoltageProbe("V(VCVS)",  n_e)
v_g  = VoltageProbe("V(VCCS)",  n_g)

ckt.AddProbe(v_in)
ckt.AddProbe(v_e)
ckt.AddProbe(v_g)

# ── simulate ─────────────────────────────────────────────────────────
ckt.Finalize()

plotter = LivePlotter(
    [v_in, v_e, v_g],   # all three waveforms overlaid
    window=30e-3,        # 3 full cycles at 100 Hz
)

sim = LiveSimulation(
    ckt, plotter,
    dt=5e-5,             # 200 samples per cycle
    speed=100,
)

sim.Run()
