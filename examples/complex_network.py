"""
Complex Multi-Stage RLC Network
=================================
Combines **series**, **ladder**, **parallel RC**, and **feedback** patterns
in a single circuit to stress-test both the MNA simulation engine and the
schematic drawer.

Topology
--------
::

    V1 (AC 10 V, 500 Hz)
      │
     (n1)────── R4 10 kΩ (feedback) ──────────────┐
      │                                            │
     R1 330 Ω                                      │
      │                                            │
     (n2)──── L1 47 mH ──(n3)── R2 1 kΩ ──(n4)───┘
      │                    │                │
     C1 10 μF            C2 1 μF          R3 2.2 kΩ ║ C3 100 nF
      │                    │                │
     GND                 GND              GND

**Stage 1 — Input filter:**  R1 + C1 form a low-pass RC at n2.
**Stage 2 — LC section:**    L1 + C2 form a resonant tank around n3.
**Stage 3 — Loaded output:** R2 couples into a parallel R3‖C3 load at n4.
**Feedback:**                R4 feeds output (n4) back to input (n1).

This creates multiple interacting time constants and a feedback loop,
exercising the MNA solver's numerical stability with backward-Euler
integration.  The schematic drawer must handle the GENERIC topology
with 5 nodes, 8 components, and several L-route connections.

Key frequencies
~~~~~~~~~~~~~~~
- RC input corner:    f₁ = 1/(2π·R1·C1)  ≈ 48 Hz
- LC resonance:       f₀ = 1/(2π·√(L1·C2)) ≈ 734 Hz
- RC output corner:   f₃ = 1/(2π·R3·C3)  ≈ 723 Hz
- Source frequency:   500 Hz (between f₁ and f₀)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import matplotlib
matplotlib.use("TkAgg")

from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.Components import Resistor, Capacitor, Inductor
from PyEEL.Components.Sources.VoltageSource import ACVoltageSource
from PyEEL.Probe import VoltageProbe, CurrentProbe
from PyEEL.LivePlotter import LivePlotter
from PyEEL.LiveSimulation import LiveSimulation
from PyEEL.SchematicDrawer import SchematicDrawer

# ════════════════════════════════════════════════════════════════════
#  Build circuit
# ════════════════════════════════════════════════════════════════════
ckt = Circuit(solver=NumpySolver())
nm  = ckt.NodeManager
gnd = nm.GroundNode

n1 = nm.AddNode("n1")   # source / feedback junction
n2 = nm.AddNode("n2")   # after input resistor
n3 = nm.AddNode("n3")   # after inductor (LC tank)
n4 = nm.AddNode("n4")   # output / load node

# ── Source ──────────────────────────────────────────────────────────
ckt.AddComponent(ACVoltageSource("V1", (n1, gnd),
                                 amplitude=10.0, frequency=500.0))

# ── Stage 1: input filter ──────────────────────────────────────────
ckt.AddComponent(Resistor("R1", (n1, n2), resistance=330.0))
ckt.AddComponent(Capacitor("C1", (n2, gnd), capacitance=10e-6))

# ── Stage 2: LC resonant section ───────────────────────────────────
ckt.AddComponent(Inductor("L1", (n2, n3), inductance=47e-3))
ckt.AddComponent(Capacitor("C2", (n3, gnd), capacitance=1e-6))

# ── Stage 3: coupled load ──────────────────────────────────────────
ckt.AddComponent(Resistor("R2", (n3, n4), resistance=1000.0))
ckt.AddComponent(Resistor("R3", (n4, gnd), resistance=2200.0))
ckt.AddComponent(Capacitor("C3", (n4, gnd), capacitance=100e-9))

# ── Feedback path ──────────────────────────────────────────────────
ckt.AddComponent(Resistor("R4", (n4, n1), resistance=10000.0))

# ════════════════════════════════════════════════════════════════════
#  Probes — measure every node voltage + key branch currents
# ════════════════════════════════════════════════════════════════════
v_n1 = VoltageProbe("V(n1)", n1)
v_n2 = VoltageProbe("V(n2)", n2)
v_n3 = VoltageProbe("V(n3)", n3)
v_n4 = VoltageProbe("V(n4)", n4)
v_lc = VoltageProbe("V_LC",  n2, n3)        # voltage across L1

i_v1  = CurrentProbe("I(V1)",  ckt._Components[0])   # source current
i_l1  = CurrentProbe("I(L1)",  ckt._Components[3])   # inductor current
i_r4  = CurrentProbe("I(R4)",  ckt._Components[8])   # feedback current

ckt.AddProbe(v_n1)
ckt.AddProbe(v_n2)
ckt.AddProbe(v_n3)
ckt.AddProbe(v_n4)
ckt.AddProbe(v_lc)
ckt.AddProbe(i_v1)
ckt.AddProbe(i_l1)
ckt.AddProbe(i_r4)

ckt.Finalize()

# ════════════════════════════════════════════════════════════════════
#  Schematic
# ════════════════════════════════════════════════════════════════════
drawer = SchematicDrawer.FromCircuit(ckt)
drawer.Summary()
drawer.Save("examples/complex_network.png")
print("Saved examples/complex_network.png")
drawer.Draw(show=True)

# ════════════════════════════════════════════════════════════════════
#  Simulation
# ════════════════════════════════════════════════════════════════════
#  dt must be small enough for the LC resonance (~734 Hz).
#  Nyquist ⇒ dt < 1/(2·734) ≈ 680 μs.  Use 50 μs for headroom.
plotter = LivePlotter(
    [v_n1, v_n2, v_n3, v_n4],
    [i_v1, i_l1, i_r4],
    window=0.01,       # 10 ms window shows ~5 cycles at 500 Hz
)
sim = LiveSimulation(ckt, plotter, dt=50e-6, speed=60)
sim.Run()
