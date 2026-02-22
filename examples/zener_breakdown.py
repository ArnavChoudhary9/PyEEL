"""
PyEEL — Zener Breakdown: Two-Resistor Voltage Divider
=======================================================
Demonstrates Zener breakdown clamping in a resistive voltage divider.

Topology::

    V1 (slow sine: 0 → 24 V → 0, 0.5 Hz)
     │
    (n_in)
     │
    R1 (1 kΩ)
     │
    (n_b) ──┬── R2 (2.2 kΩ) ── GND
            │
           DZ1  ← Zener 5.1 V
            │     (cathode = n_b, anode = GND)
           GND

How breakdown clamping works
-----------------------------
Without the Zener, the divider sets::

    V(n_b) = V_supply × R2 / (R1 + R2)  ≈  0.69 × V_supply

The Zener allows this voltage to rise freely until it hits 5.1 V.
For supply voltages above ~7.4 V the Zener enters breakdown, clamping
n_b at 5.1 V and diverting excess current through itself.

The slow 0.5 Hz sine (DC-offset so it sweeps 0 V → 24 V → 0 V)
makes the knee transition visible on the live plot:

  • Low supply  → V(n_b) tracks the divider ratio (linear)
  • High supply → V(n_b) is clamped at 5.1 V (flat top)

Probes
------
  • V(n_in)  — supply voltage (input)
  • V(n_b)   — divider / Zener output node
  • I(DZ1)   — Zener current (zero below knee, rises sharply above it)
"""

from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.SimulationContext import SimulationConfig
from PyEEL.Components import Resistor
from PyEEL.Components.ZenerDiode import ZenerDiode
from PyEEL.Components.Sources.VoltageSource import VoltageSource
from PyEEL.Components.Sources.Waveform import SineWave
from PyEEL.Probe import VoltageProbe, CurrentProbe
from PyEEL.LivePlotter import LivePlotter
from PyEEL.LiveSimulation import LiveSimulation

# ── simulation config ────────────────────────────────────────────────
config = SimulationConfig(
    dc_operating_point=True,
    gmin=1e-12,
)

# ── build circuit ────────────────────────────────────────────────────
ckt = Circuit(solver=NumpySolver(), config=config)

nm   = ckt.NodeManager
gnd  = nm.GroundNode
n_in = nm.AddNode("n_in")   # supply rail
n_b  = nm.AddNode("n_b")    # divider mid-point / Zener cathode

# ── slowly sweeping supply: 0 Hz offset + 12 V amplitude + 12 V DC
#    → waveform = 12 + 12·sin(2π·0.5·t)  sweeps 0 V … 24 V at 0.5 Hz
ckt.AddComponent(VoltageSource("V1", (n_in, gnd),
                                waveform=SineWave(frequency=0.5,
                                                  amplitude=12.0,
                                                  dc_offset=12.0)))

# ── resistive divider ───────────────────────────────────────────────
ckt.AddComponent(Resistor("R1", (n_in, n_b), resistance=1e3))
ckt.AddComponent(Resistor("R2", (n_b, gnd),  resistance=2.2e3))

# ── Zener clamp: cathode at n_b, anode at GND (reverse biased) ──────
ckt.AddComponent(dz1 := ZenerDiode("DZ1", (gnd, n_b),
                                    Vz=5.1, Ibv=5e-3, n_bv=0.5))

# ── probes ───────────────────────────────────────────────────────────
v_in  = VoltageProbe("V(supply)", n_in)   # sweeping input
v_b   = VoltageProbe("V(output)", n_b)    # clamped divider output
i_dz1 = CurrentProbe("I(DZ1)",    dz1)    # Zener breakdown current

ckt.AddProbe(v_in)
ckt.AddProbe(v_b)
ckt.AddProbe(i_dz1)

# ── live simulation ──────────────────────────────────────────────────
ckt.Finalize()

plotter = LivePlotter(
    [v_in, v_b],    # subplot 1: supply vs clamped output (knee visible)
    [i_dz1],        # subplot 2: Zener current (jumps at breakdown)
    window=2.0,     # show last 2 s (one full 0.5 Hz cycle)
)

sim = LiveSimulation(
    ckt, plotter,
    dt=1e-3,        # 1 ms step
    speed=20,
)

sim.Run()
