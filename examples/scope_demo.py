"""
PyEEL — Scope Demo (Half-Wave Rectifier)
=========================================
Same circuit as ``half_wave_rectifier.py`` but uses the **Scope**
module instead of LivePlotter.  Because both implement the same
protocol, ``LiveSimulation`` works with either one.

Swap guide::

    # LivePlotter (matplotlib) ──────────────────
    plotter = LivePlotter([v_in, v_out], [i_d1], window=0.1)
    sim = LiveSimulation(ckt, plotter, dt=1e-4, speed=100)
    sim.Run()

    # Scope (PyQt6 / pyqtgraph) ────────────────
    scope = Scope([v_in, v_out], [i_d1], window=0.1)
    sim = LiveSimulation(ckt, scope, dt=1e-4, speed=100)
    sim.Run()
"""

from PyEEL import *

# ── config ──────────────────────────────────────────────────────────
config = SimulationConfig(
    dc_operating_point=True,
    gmin=1e-12,
)

# ── circuit ─────────────────────────────────────────────────────────
ckt = Circuit(solver=NumpySolver(), config=config)

nm  = ckt.NodeManager
gnd = nm.GroundNode
n1  = nm.AddNode("n1")
n2  = nm.AddNode("n2")

ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=5.0, frequency=50.0))
ckt.AddComponent(d1 := Diode("D1", (n1, n2)))
ckt.AddComponent(Resistor("R1", (n2, gnd), resistance=1000.0))

v_in  = VoltageProbe("V_in", n1)
v_out = VoltageProbe("V_out", n2)
i_d1  = CurrentProbe("I_D1", d1)

ckt.AddProbe(v_in)
ckt.AddProbe(v_out)
ckt.AddProbe(i_d1)

ckt.Finalize()

# ── launch Scope via LiveSimulation ─────────────────────────────────
scope = Scope(
    [v_in, v_out],
    [i_d1],
    window=0.1,
    trigger_level=0.0,
    trigger_edge=TriggerEdge.RISING,
    trigger_mode=TriggerMode.AUTO,
    trigger_source=0,
    show_measurements=True,
    title="Scope — Half-Wave Rectifier",
)

sim = LiveSimulation(
    ckt, scope,
    dt=1e-4,
    speed=100,
)

sim.Run()
