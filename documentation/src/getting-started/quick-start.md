# Quick Start

This page walks through building and simulating a simple circuit — an AC
source driving a resistor — in under 30 lines of code.

## 1. Imports

```python
from PyEEL import (
    Circuit, NumpySolver, SimulationConfig,
    Resistor, ACVoltageSource,
    VoltageProbe, CurrentProbe,
    LivePlotter, LiveSimulation,
)
```

## 2. Create the Circuit

```python
config = SimulationConfig(dc_operating_point=True)
ckt    = Circuit(solver=NumpySolver(), config=config)
nm     = ckt.NodeManager
gnd    = nm.GroundNode
```

- **`NumpySolver()`** — the linear algebra back-end (NumPy dense solver).
- **`SimulationConfig`** — holds every simulation knob (defaults are fine for
  most circuits).
- **`NodeManager`** — creates and tracks circuit nodes.  `GroundNode` is the
  reference (0 V).

## 3. Add Nodes and Components

```python
n1 = nm.AddNode("n1")    # top of the resistor
n2 = nm.AddNode("n2")    # bottom of the resistor (optional mid-node)

ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=5, frequency=50))
ckt.AddComponent(Resistor("R1", (n1, gnd), resistance=1000))
```

Every component needs:

1. A **unique name** (string)
2. A **tuple of `Node` objects** defining its terminals
3. Its **electrical parameters**

## 4. Add Probes

```python
v_probe = VoltageProbe("V_n1", n1)           # voltage at n1 vs GND
i_probe = CurrentProbe("I_V1", ckt.????)     # explained below
ckt.AddProbe(v_probe)
```

- **`VoltageProbe(name, node)`** records `V(node) - V(GND)` at every time step.
- **`CurrentProbe(name, component)`** records the branch current through a
  voltage source (or any component that stores an auxiliary current unknown).

## 5. Finalize & Simulate

```python
ckt.Finalize()   # freeze topology, allocate MNA matrices

# Option A — live animated plot
plotter = LivePlotter([v_probe], window=0.1)
sim     = LiveSimulation(ckt, plotter, dt=1e-4, speed=100)
sim.Run()         # blocks until window is closed

# Option B — headless loop
for _ in range(10_000):
    ckt.Simulate(dt=1e-4)
print(v_probe.ValueData[-1])     # last recorded value
```

## The Standard Pattern

Almost every PyEEL script follows this sequence:

```
Config → Circuit → NodeManager → Nodes → Components → Probes → Finalize → Simulate
```

| Step | Key Call |
|---|---|
| Config | `SimulationConfig(...)` |
| Circuit | `Circuit(solver=NumpySolver(), config=config)` |
| Nodes | `nm.AddNode("name")` |
| Components | `ckt.AddComponent(...)` |
| Probes | `ckt.AddProbe(VoltageProbe(...))` |
| Finalize | `ckt.Finalize()` |
| Simulate | `LiveSimulation(...).Run()` or `ckt.Simulate(dt)` loop |
