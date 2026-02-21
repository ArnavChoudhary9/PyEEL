from PyEEL.Circuit import Circuit
from PyEEL.LivePlotter import LivePlotter
from PyEEL.LiveSimulation import LiveSimulation
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.Components import Resistor
from PyEEL.Components.Transformer import Transformer
from PyEEL.Components.Sources.VoltageSource import ACVoltageSource
from PyEEL.Probe import VoltageProbe, CurrentProbe

ckt = Circuit(solver=NumpySolver())
nm  = ckt.NodeManager
gnd = nm.GroundNode
n1 = nm.AddNode('n1'); n2 = nm.AddNode('n2'); n3 = nm.AddNode('n3')

ckt.AddComponent(ACVoltageSource('V1', (n1, gnd), amplitude=240.0, frequency=50.0))
ckt.AddComponent(Resistor('R_primary', (n1, n2), resistance=100.0))
T1 = Transformer('T1',
    primary_nodes=(n2, gnd),
    secondary_nodes=(gnd, n3),
    primary_inductance=2.304,
    secondary_inductance=1e-3,
    k=0.99)
ckt.AddComponent(T1)
ckt.AddComponent(Resistor('R_load', (n3, gnd), resistance=5.0))

v_sec = VoltageProbe('V_sec', n3)
i_pri = CurrentProbe('I_pri', T1.Primary)
i_sec = CurrentProbe('I_sec', T1.Secondary)
ckt.AddProbe(v_sec); ckt.AddProbe(i_pri); ckt.AddProbe(i_sec)
ckt.Finalize()

plotter = LivePlotter(
    [v_sec],
    [i_pri, i_sec],
    window=0.1,
)
sim = LiveSimulation(ckt, plotter, dt=1e-4, speed=60)
