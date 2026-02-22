# Adding New Components

This guide shows how to implement a new component type in PyEEL by
subclassing `Component`.

## Step 1 — Subclass `Component`

```python
from PyEEL.Components.Component import Component
from PyEEL.Core.Node import Node
from PyEEL.Core.NodeManager import NodeManager
from PyEEL.Core.SimulationContext import SimulationContext, SimulationMode
import numpy as np


class MyComponent(Component):
    """My custom component."""

    def __init__(self, name: str, nodes: tuple[Node, Node], my_param: float):
        super().__init__(name, nodes)
        self._my_param = my_param
```

## Step 2 — Implement the Five Abstract Methods

### `RegisterUnknowns`

Request auxiliary unknowns if your component needs branch currents:

```python
def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
    # Only needed for voltage-forcing elements (voltage sources, inductors)
    # For conductance-only elements (resistors, diodes), do nothing:
    pass
```

### `Stamp`

Write your component's contribution into the MNA matrix:

```python
def Stamp(self, A: np.ndarray, b: np.ndarray,
          context: SimulationContext) -> None:
    n1, n2 = self.Nodes
    G = 1.0 / self._my_param  # example: conductance

    # Stamp conductance (same pattern as Resistor)
    if n1.Index is not None:
        A[n1.Index, n1.Index] += G
        if n2.Index is not None:
            A[n1.Index, n2.Index] -= G
    if n2.Index is not None:
        A[n2.Index, n2.Index] += G
        if n1.Index is not None:
            A[n2.Index, n1.Index] -= G
```

### `UpdateState`

Store any state needed for the next time step:

```python
def UpdateState(self, solutionVector: np.ndarray,
                context: SimulationContext) -> None:
    # For memoryless components, do nothing.
    # For stateful components (capacitors, inductors), save history.
    pass
```

### `GetCurrent` and `GetVoltage`

```python
def GetCurrent(self, solutionVector: np.ndarray) -> float:
    v = self.GetVoltage(solutionVector)
    return v / self._my_param

def GetVoltage(self, solutionVector: np.ndarray) -> float:
    n1, n2 = self.Nodes
    v1 = solutionVector[n1.Index] if n1.Index is not None else 0.0
    v2 = solutionVector[n2.Index] if n2.Index is not None else 0.0
    return float(v1 - v2)
```

## Step 3 — Non-Linear Components

For non-linear devices, set `IsNonlinear = True` and stamp a linearised
companion model:

```python
class MyNonlinearDevice(Component):
    def __init__(self, name, nodes, ...):
        super().__init__(name, nodes)
        self.IsNonlinear = True

    def Stamp(self, A, b, context):
        # Read current operating point
        vd = get_voltage_across(context.x_current, self.Nodes[0], self.Nodes[1])

        # Compute device current and derivative
        i_d = my_equation(vd)
        g_d = my_derivative(vd)

        # Stamp linearised companion: i = g_d * v + (i_d - g_d * vd)
        i_eq = i_d - g_d * vd
        stamp_conductance(A, self.Nodes[0], self.Nodes[1], g_d)
        stamp_current_source(b, self.Nodes[0], self.Nodes[1], i_eq)
```

## Step 4 — Place the File

Put your component in the appropriate subdirectory:

- `Components/Passive/` — Linear, passive elements
- `Components/Semiconductors/` — Non-linear semiconductor devices
- `Components/Magnetic/` — Coupled magnetic components
- `Components/Sources/` — Source elements

Then add it to the relevant `__init__.py` for export.

## Step 5 — Handling DC vs Transient

Check `context.Mode` to behave differently in DC analysis:

```python
def Stamp(self, A, b, context):
    if context.Mode == SimulationMode.DC:
        # DC behaviour (e.g. capacitor = open, inductor = short)
        ...
    else:
        # Transient behaviour with companion model
        ...
```

## Stamp Helpers

Use the utilities in `Components.stamp_helpers`:

```python
from PyEEL.Components.stamp_helpers import (
    stamp_conductance,
    stamp_transconductance,
    stamp_current_source,
    get_voltage_across,
)
```

These handle the ground-node checks automatically.
