# Components Overview

All circuit elements in PyEEL inherit from the abstract `Component` base
class.  Every component must implement five methods that the MNA engine
calls during simulation.

## Base Class: `Component`

```python
from PyEEL.Components.Component import Component
```

### Constructor

```python
Component(name: str, nodes: tuple[Node, ...], aux_indices: list[int] | None = None)
```

| Argument | Description |
|---|---|
| `name` | Unique identifier string (e.g. `"R1"`, `"D1"`) |
| `nodes` | Tuple of `Node` objects — the component's terminals |
| `aux_indices` | Pre-existing auxiliary variable indices (rarely used) |

### Properties

| Property | Type | Description |
|---|---|---|
| `Name` | `str` | Component name |
| `Nodes` | `tuple[Node, ...]` | Terminal nodes |
| `AuxIndices` | `list[int]` | Auxiliary unknown indices (branch currents) |
| `PreviousState` | `dict` | Persistent state between time steps |
| `IsNonlinear` | `bool` | `False` by default; `True` for diodes, BJTs, MOSFETs |

### Abstract Methods

Every component implements these:

| Method | Purpose |
|---|---|
| `RegisterUnknowns(nodeManager)` | Request auxiliary unknowns (e.g. branch current for voltage sources) |
| `Stamp(A, b, context)` | Write the component's contribution into the MNA matrix `A` and RHS vector `b` |
| `UpdateState(solutionVector, context)` | Store state needed for the next time step (e.g. capacitor voltage) |
| `GetCurrent(solutionVector)` | Return the branch current through the component |
| `GetVoltage(solutionVector)` | Return the voltage across the component |

## Component Categories

| Category | Components | Module |
|---|---|---|
| **Passive** | Resistor, Capacitor, Inductor | `Components.Passive` |
| **Semiconductors** | Diode, ZenerDiode, BJT, MOSFET | `Components.Semiconductors` |
| **Magnetic** | MutualCoupling, Transformer | `Components.Magnetic` |
| **Sources** | VoltageSource, VCVS, VCCS, CCVS, CCCS | `Components.Sources` |

## Stamp Helpers

Utility functions in `Components.stamp_helpers` simplify writing MNA stamps:

```python
stamp_conductance(A, na, nb, G)          # 2×2 conductance stamp
stamp_transconductance(A, ...)           # VCCS-style stamp
stamp_current_source(b, n_from, n_to, I) # current into RHS
get_voltage_across(solution, n_pos, n_neg)
```
