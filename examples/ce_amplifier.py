"""
PyEEL — Common-Emitter BJT Amplifier
=====================================
Demonstrates the BJT component in a voltage-divider-biased
common-emitter amplifier configuration.

Topology::

         VCC (+12 V)
          │       │
         R1      RC  (4.7 kΩ)
        (56 kΩ)   │
          │       ├── n_out
          │       │
    n_b ──┤  Q1  (NPN, β = 100)
          │       │
         R2      RE  (1 kΩ)
        (12 kΩ)   │
          │       │
         GND     GND

    V_in (1 kHz, 20 mV peak) ── C1 (10 µF) ── n_b

Bias point (approximate):
  • V_B  ≈ 2.12 V    (voltage divider)
  • V_E  ≈ 1.42 V    (V_B - V_BE)
  • I_C  ≈ 1.42 mA
  • V_C  ≈ 5.33 V    (VCC - I_C · RC)

Small-signal voltage gain  ≈  -RC / (RE + r_e)  ≈  -4.6
where  r_e = V_t / I_C  ≈ 18 Ω.

Probes:
  • V(n_b)   — base voltage (input)
  • V(n_out) — collector voltage (output)
  • I(Q1)    — collector current
"""

from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.SimulationContext import SimulationConfig
from PyEEL.Components import Resistor, Capacitor
from PyEEL.Components.BJT import NPN
from PyEEL.Components.Sources.VoltageSource import DCVoltageSource, ACVoltageSource
from PyEEL.Probe import VoltageProbe, CurrentProbe
from PyEEL.LivePlotter import LivePlotter
from PyEEL.LiveSimulation import LiveSimulation

# ── simulation config ───────────────────────────────────────────────
config = SimulationConfig(
    dc_operating_point=True,
    gmin=1e-12,
)

# ── build circuit ───────────────────────────────────────────────────
ckt = Circuit(solver=NumpySolver(), config=config)

nm  = ckt.NodeManager
gnd = nm.GroundNode
n_vcc = nm.AddNode("n_vcc")       # supply rail
n_b   = nm.AddNode("n_b")         # base node
n_c   = nm.AddNode("n_c")         # collector node
n_e   = nm.AddNode("n_e")         # emitter node
n_in  = nm.AddNode("n_in")        # AC input node
n_out = nm.AddNode("n_out")       # AC output node

# ── DC supply ───────────────────────────────────────────────────────
ckt.AddComponent(DCVoltageSource("VCC", (n_vcc, gnd), voltage=12.0))

# ── bias network (voltage divider) ─────────────────────────────────
ckt.AddComponent(Resistor("R1", (n_vcc, n_b), resistance=56e3))
ckt.AddComponent(Resistor("R2", (n_b, gnd),   resistance=12e3))

# ── transistor ──────────────────────────────────────────────────────
q1 = NPN("Q1", (n_c, n_b, n_e), BF=100.0)
ckt.AddComponent(q1)

# ── collector and emitter resistors ─────────────────────────────────
ckt.AddComponent(Resistor("RC", (n_vcc, n_c), resistance=4.7e3))
ckt.AddComponent(Resistor("RE", (n_e, gnd),   resistance=1e3))

# ── AC input (coupling capacitor + signal source) ───────────────────
ckt.AddComponent(ACVoltageSource("V_in", (n_in, gnd),
                                  amplitude=0.02, frequency=1000.0))
ckt.AddComponent(Capacitor("C1", (n_in, n_b), capacitance=10e-6))

# ── AC output coupling capacitor ────────────────────────────────────
ckt.AddComponent(Capacitor("C2", (n_c, n_out), capacitance=10e-6))
ckt.AddComponent(Resistor("R_load", (n_out, gnd), resistance=10e3))

# ── probes ──────────────────────────────────────────────────────────
v_in   = VoltageProbe("V(in)",  n_in)        # input signal
v_base = VoltageProbe("V(base)", n_b)        # base voltage
v_out  = VoltageProbe("V(out)", n_out)       # amplified output
i_c    = CurrentProbe("I(Q1)",  q1)          # collector current

ckt.AddProbe(v_in)
ckt.AddProbe(v_base)
ckt.AddProbe(v_out)
ckt.AddProbe(i_c)

# ── simulate ────────────────────────────────────────────────────────
ckt.Finalize()

plotter = LivePlotter(
    [v_in, v_out],           # subplot 1: input vs amplified output
    [v_base],                # subplot 2: base DC bias + AC ripple
    [i_c],                   # subplot 3: collector current
    window=5e-3,             # show last 5 ms (5 cycles at 1 kHz)
)

sim = LiveSimulation(
    ckt, plotter,
    dt=5e-6,                 # 5 µs step → 200 samples per 1 kHz cycle
    speed=200,               # steps per frame
)

sim.Run()
