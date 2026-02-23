# PyEEL — Python Electronics Engineering Library

**PyEEL** is a from-scratch circuit simulator written in pure Python (NumPy).
It implements **Modified Nodal Analysis (MNA)** with a full **Newton–Raphson**
non-linear solver, **Backward-Euler** transient integration, and real-time
**matplotlib** visualisation — all in a clean, extensible object-oriented
design.

## What Can It Do?

| Capability | Details |
|---|---|
| **DC operating-point** | Solves the steady-state bias point of any circuit |
| **Transient analysis** | Time-domain simulation with fixed or adaptive time-step |
| **Non-linear devices** | Diodes, Zener diodes, BJTs (Ebers–Moll), MOSFETs (Level-1) |
| **Magnetic coupling** | Coupled inductors, ideal transformers |
| **Dependent sources** | VCVS, VCCS, CCVS, CCCS |
| **Live visualisation** | Real-time animated plots with `LiveSimulation` |
| **Pre-built library** | 165+ real-world components with datasheet parameters |

## Project Layout

```
PyEEL/
├── Core/                  # Node, NodeManager, SimulationContext
├── Components/
│   ├── Passive/           # Resistor, Capacitor, Inductor
│   ├── Semiconductors/    # Diode, ZenerDiode, BJT, MOSFET
│   ├── Magnetic/          # MutualCoupling, Transformer
│   ├── Sources/           # VoltageSource, DependentSources, Waveform
│   ├── common/            # Circuit-topology factory helpers
│   └── library/           # Pre-built real-world parts (typed)
├── Solver/                # MNA builder, Newton–Raphson, DC OP
├── Simulation/            # Circuit engine, adaptive timestep
└── Visualization/         # Probes, LivePlotter, LiveSimulation
```

## Quick Example

```python
from PyEEL import (
    Circuit, NumpySolver, SimulationConfig,
    Resistor, ACVoltageSource, Diode,
    VoltageProbe, LivePlotter, LiveSimulation,
)

config = SimulationConfig(dc_operating_point=True)
ckt    = Circuit(solver=NumpySolver(), config=config)
nm     = ckt.NodeManager
gnd    = nm.GroundNode

n1  = nm.AddNode("n1")
n2  = nm.AddNode("n2")

ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=5, frequency=50))
ckt.AddComponent(Diode("D1", (n1, n2)))
ckt.AddComponent(Resistor("R1", (n2, gnd), resistance=1000))

ckt.AddProbe(VoltageProbe("V_in", n1))
ckt.AddProbe(VoltageProbe("V_out", n2))
ckt.Finalize()

plotter = LivePlotter([ckt.Probes[0], ckt.Probes[1]])
sim     = LiveSimulation(ckt, plotter, dt=1e-4, speed=100)
sim.Run()
```

> **Next:** [Installation →](getting-started/installation.md)
