"""
PyEEL — Zener Diode AC Clipper (Asymmetric Rectifier)
=======================================================
Demonstrates how a single Zener diode clamps an AC signal in two
distinct ways on each half-cycle, producing an asymmetrically
clipped (rectified) waveform.

Topology::

    V1 (AC 10 V peak, 50 Hz)
     │
    (n_in)
     │
    R_series (1 kΩ)  ← current limiter
     │
    (n_out) ──── R_load (10 kΩ) ──── GND
     │
    DZ1 (Vz = 5 V)
     │     cathode = n_out
     │     anode   = GND
    GND

How the clipping works
-----------------------
**Positive half-cycle** (V_in > 0):

  DZ1 is reverse biased.  Once V(n_out) reaches **+5 V** the Zener
  enters breakdown, clamping the output at +5 V.  Any additional
  current from the source flows through R_series and into the Zener.

**Negative half-cycle** (V_in < 0):

  DZ1 is forward biased like a normal diode.  Once V(n_out) drops
  below **≈ -0.7 V** the Zener conducts in the forward direction,
  clamping the output at ~-0.7 V.

The result is a waveform clipped between **-0.7 V** and **+5 V** —
an asymmetric clipper / half-wave-like rectifier with a defined
upper breakdown threshold.

Probes
------
  • V(n_in)  — original ±10 V sine wave (input)
  • V(n_out) — clipped output: flat top at +5 V, flat bottom at -0.7 V
  • I(DZ1)   — Zener current (positive = forward, negative = breakdown)
"""

from PyEEL import *

# ── simulation config ────────────────────────────────────────────────
config = SimulationConfig(
    dc_operating_point=True,
    gmin=1e-12,
)

# ── build circuit ────────────────────────────────────────────────────
ckt = Circuit(solver=NumpySolver(), config=config)

nm    = ckt.NodeManager
gnd   = nm.GroundNode
n_in  = nm.AddNode("n_in")    # raw AC input
n_out = nm.AddNode("n_out")   # clipped output

# ── 50 Hz, ±10 V AC source ──────────────────────────────────────────
ckt.AddComponent(ACVoltageSource("V1", (n_in, gnd),
                                  amplitude=10.0, frequency=50.0))

# ── series current-limiting resistor ────────────────────────────────
ckt.AddComponent(Resistor("R_series", (n_in, n_out), resistance=1e3))

# ── Zener clamp: cathode = n_out, anode = GND
#    Breakdown (reverse) at +5 V  →  clamps positive peaks at +5 V
#    Forward conduction at ~-0.7 V →  clamps negative peaks at -0.7 V
ckt.AddComponent(dz1 := ZenerDiode("DZ1", (gnd, n_out),
                                    Vz=5.0, Ibv=10e-3, n_bv=0.5))

# ── load resistor ────────────────────────────────────────────────────
ckt.AddComponent(Resistor("R_load", (n_out, gnd), resistance=10e3))

# ── probes ───────────────────────────────────────────────────────────
v_in  = VoltageProbe("V(input)",  n_in)    # ±10 V sine input
v_out = VoltageProbe("V(clipped)", n_out)  # clipped output
i_dz1 = CurrentProbe("I(DZ1)",    dz1)    # Zener current

ckt.AddProbe(v_in)
ckt.AddProbe(v_out)
ckt.AddProbe(i_dz1)

# ── live simulation ──────────────────────────────────────────────────
ckt.Finalize()

plotter = LivePlotter(
    [v_in, v_out],  # subplot 1: full sine vs clipped output
    [i_dz1],        # subplot 2: Zener current (forward/breakdown phases)
    window=60e-3,   # show last 60 ms (3 full cycles at 50 Hz)
)

sim = LiveSimulation(
    ckt, plotter,
    dt=1e-4,        # 0.1 ms step → 200 samples per 50 Hz cycle
    speed=50,
)

sim.Run()
