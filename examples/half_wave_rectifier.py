"""
PyEEL — Half-Wave Rectifier Demo
==================================
Demonstrates a nonlinear circuit containing a diode.

Topology::

    V1 (AC 5 V, 50 Hz)
     ├──(n1)── D1 (diode, anode→cathode) ──(n2)── R1 1 kΩ ──(GND)

The diode conducts only on positive half-cycles, producing a
half-wave rectified waveform across the load resistor R1.

Probes:
  • V(n1)  — source (input) voltage
  • V(n2)  — rectified (output) voltage across R1
  • I(D1)  — diode current
"""

from PyEEL import *

# ── simulation config (NR defaults are fine) ────────────────────────
config = SimulationConfig(
    dc_operating_point=True,
    gmin=1e-12,
)

# ── build circuit ───────────────────────────────────────────────────
ckt = Circuit(solver=NumpySolver(), config=config)

nm  = ckt.NodeManager
gnd = nm.GroundNode
n1  = nm.AddNode("n1")
n2  = nm.AddNode("n2")

#  V1 ──(n1)── D1 ──(n2)── R1 ──(GND)
ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=5.0, frequency=50.0))
ckt.AddComponent(d1 := Diode("D1", (n1, n2)))
ckt.AddComponent(Resistor("R1", (n2, gnd), resistance=1000.0))

# ── probes ──────────────────────────────────────────────────────────
v_in  = VoltageProbe("V(n1)", n1)       # input voltage
v_out = VoltageProbe("V(n2)", n2)       # rectified output
i_d1  = CurrentProbe("I(D1)", d1)       # diode current

ckt.AddProbe(v_in)
ckt.AddProbe(v_out)
ckt.AddProbe(i_d1)

# ── simulate ────────────────────────────────────────────────────────
ckt.Finalize()

plotter = LivePlotter(
    [v_in, v_out],
    [i_d1],
    window=100e-3,   # show last 100 ms (5 cycles at 50 Hz)
)

sim = LiveSimulation(
    ckt, plotter,
    dt=1e-4,
    speed=100,
)

sim.Run()
