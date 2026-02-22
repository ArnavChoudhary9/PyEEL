"""
PyEEL - Inverting Op-Amp Amplifier
===================================
Demonstrates the OpAmp component in an inverting amplifier
configuration with transient simulation and live plotting.

Topology::

              Rf = 100 kOhm
         +----/\\/\\/----+
         |             |
Vin -- Rin (10 kOhm) -+(-) U1   |
                       |      +--+-- Vout
                   GND--(+)      |
                                 |
                       Rload (10 kOhm) -- GND

Gain = -Rf / Rin = -100k / 10k = -10

With Vin = 0.5 V peak (1 kHz) -> Vout = -5 V peak (inverted)
"""

from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.SimulationContext import SimulationConfig
from PyEEL.Components import Resistor, OpAmp
from PyEEL.Components.Sources.VoltageSource import ACVoltageSource
from PyEEL.Probe import VoltageProbe
from PyEEL.LivePlotter import LivePlotter
from PyEEL.LiveSimulation import LiveSimulation

# -- simulation config -----------------------------------------------
config = SimulationConfig(
    dc_operating_point=True,
    gmin=1e-12,
)

# -- build circuit ----------------------------------------------------
ckt = Circuit(solver=NumpySolver(), config=config)

nm  = ckt.NodeManager
gnd = nm.GroundNode
n_in  = nm.AddNode("n_in")
n_inv = nm.AddNode("n_inv")      # inverting input junction
n_out = nm.AddNode("n_out")

# 1 kHz, 0.5 V peak sine input
ckt.AddComponent(ACVoltageSource("Vin", (n_in, gnd),
                                 amplitude=0.5, frequency=1000.0))

# Inverting amplifier
ckt.AddComponent(Resistor("Rin",   (n_in, n_inv), resistance=10e3))
ckt.AddComponent(Resistor("Rf",    (n_inv, n_out), resistance=100e3))
ckt.AddComponent(OpAmp("U1",       (gnd, n_inv, n_out)))

# Load resistor (prevents floating output)
ckt.AddComponent(Resistor("Rload", (n_out, gnd), resistance=10e3))

# -- probes -----------------------------------------------------------
p_in  = VoltageProbe("V_in",  n_in)
p_out = VoltageProbe("V_out", n_out)
ckt.AddProbe(p_in)
ckt.AddProbe(p_out)

# -- live simulation --------------------------------------------------
ckt.Finalize()

plotter = LivePlotter(
    [p_in, p_out],        # subplot 1: input vs output (inverted & amplified)
    window=3e-3,          # show last 3 ms (3 cycles at 1 kHz)
)

sim = LiveSimulation(
    ckt, plotter,
    dt=2e-6,              # 2 us step -> 500 samples per 1 kHz cycle
    speed=100,            # steps per frame
)

sim.Run()

