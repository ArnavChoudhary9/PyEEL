# Circuit

The `Circuit` class is the top-level simulation engine.  It owns the node
manager, component list, probes, and drives the MNA solve loop.

```python
from PyEEL import Circuit, NumpySolver, SimulationConfig

config = SimulationConfig(dc_operating_point=True)
ckt    = Circuit(solver=NumpySolver(), config=config)
```

## Constructor

```python
Circuit(solver: LinearSolver, config: SimulationConfig | None = None)
```

| Argument | Description |
|---|---|
| `solver` | A `LinearSolver` instance (use `NumpySolver()`) |
| `config` | Optional simulation configuration.  Defaults are used if omitted. |

## Properties

| Property | Type | Description |
|---|---|---|
| `NodeManager` | `NodeManager` | Access the node factory |
| `Time` | `float` | Current simulation clock (seconds) |
| `Probes` | `list[Probe]` | All registered probes |
| `Config` | `SimulationConfig` | Active configuration |
| `RecommendedDt` | `float` | Suggested time step based on circuit dynamics |

## Building a Circuit

### Step 1 — Create Nodes

```python
nm  = ckt.NodeManager
gnd = nm.GroundNode
n1  = nm.AddNode("n1")
n2  = nm.AddNode("n2")
```

### Step 2 — Add Components

```python
ckt.AddComponent(Resistor("R1", (n1, gnd), resistance=1000))
ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=5, frequency=50))
```

### Step 3 — Add Probes

```python
ckt.AddProbe(VoltageProbe("V_n1", n1))
```

### Step 4 — Finalize

```python
ckt.Finalize()
```

`Finalize()` performs these critical steps in order:

1. **Freezes the node manager** — no more nodes can be added.
2. **Registers auxiliary unknowns** — voltage sources and current-controlled
   sources get their branch-current indices.
3. **Validates topology** — checks for isolated nodes, capacitor-only nodes,
   voltage-source loops, and extreme parameter values.
4. **Allocates MNA arrays** — creates the `A` matrix and `b` vector sized to
   `TotalUnknownCount`.
5. **Creates the Newton–Raphson solver** (if non-linear components exist).

## Simulating

### DC Operating Point

```python
x_dc = ckt.SolveDCOperatingPoint()
```

Solves the static bias point with all time-derivative terms zeroed.
Capacitors become open circuits; inductors become short circuits.

### Transient Step

```python
x = ckt.Simulate(dt=1e-4)
```

Advances the simulation by one time step `dt`.  Returns the new solution
vector.  Internally:

1. Builds the MNA system for the current time.
2. If the circuit is linear, solves directly; otherwise runs
   Newton–Raphson.
3. Updates component internal states (e.g. capacitor history).
4. Records probe data.
5. Advances the clock.

### Reset

```python
ckt.Reset()
```

Resets the simulation clock to 0, clears the solution vector, and
clears all probe data.  The topology and components remain intact, so
you can re-run without rebuilding.
