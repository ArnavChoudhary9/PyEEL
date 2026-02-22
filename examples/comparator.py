"""
PyEEL - Voltage Comparator
===========================
Demonstrates the Comparator component with a sine-wave input and a
fixed DC reference.  The output rail-to-rail switches between V_low
(0 V) and V_high (5 V) each time the input crosses the reference.

Topology::

    Vin (sine, 100 Hz, 2 V peak)
          |
         (+) U1  -------- n_out
          |
    Vref (1 V DC) -- (-) U1
                           |
                     Rload (10 kOhm) -- GND

    V_out = 5 V  when V_in > V_ref (1 V)
    V_out = 0 V  when V_in < V_ref (1 V)

With V_ref = 1 V the comparator is positive for most of the positive
half-cycle and all of the negative half-cycle it is below reference,
so the duty cycle is <50 %.

Press Ctrl-C to stop the simulation.
"""

from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.SimulationContext import SimulationConfig
from PyEEL.Components.ICs.Comparator import Comparator
from PyEEL.Components import Resistor
from PyEEL.Components.Sources.VoltageSource import ACVoltageSource, DCVoltageSource
from PyEEL.Probe import VoltageProbe
from PyEEL.LivePlotter import LivePlotter
from PyEEL.LiveSimulation import LiveSimulation

# -- simulation config -----------------------------------------------
config = SimulationConfig(
    dc_operating_point=True,
    gmin=1e-12,
)

# -- build circuit ---------------------------------------------------
ckt = Circuit(solver=NumpySolver(), config=config)

nm  = ckt.NodeManager
gnd = nm.GroundNode

n_in  = nm.AddNode("n_in")     # AC input
n_ref = nm.AddNode("n_ref")    # DC reference
n_out = nm.AddNode("n_out")    # comparator output

# 100 Hz, 2 V peak sine input
ckt.AddComponent(ACVoltageSource("Vin",  (n_in,  gnd),
                                  amplitude=2.0, frequency=100.0))

# 1 V DC reference
ckt.AddComponent(DCVoltageSource("Vref", (n_ref, gnd), voltage=1.0))

# Comparator: output is 5 V when Vin > Vref, else 0 V
ckt.AddComponent(Comparator("U1", (n_in, n_ref, n_out),
                              V_high=5.0, V_low=0.0))

# Load resistor to prevent floating output node
ckt.AddComponent(Resistor("Rload", (n_out, gnd), resistance=10e3))

# -- probes ----------------------------------------------------------
p_in  = VoltageProbe("V_in",  n_in)
p_ref = VoltageProbe("V_ref", n_ref)
p_out = VoltageProbe("V_out", n_out)
ckt.AddProbe(p_in)
ckt.AddProbe(p_ref)
ckt.AddProbe(p_out)

# -- live simulation -------------------------------------------------
ckt.Finalize()

plotter = LivePlotter(
    [p_in, p_ref],   # subplot 1: input signal and reference level
    [p_out],         # subplot 2: comparator digital output
    window=30e-3,    # show last 30 ms (3 full 100 Hz cycles)
)

sim = LiveSimulation(
    ckt, plotter,
    dt=10e-6,        # 10 us step  ->  1000 samples per 100 Hz cycle
    speed=50,        # steps per frame
)

sim.Run()
