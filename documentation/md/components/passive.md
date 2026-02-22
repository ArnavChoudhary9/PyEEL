# Passive Components

Passive components dissipate or store energy — they do not amplify signals.
PyEEL provides three passive elements: **Resistor**, **Capacitor**, and
**Inductor**.

All passive components are linear and stamp directly into the MNA matrix
without requiring Newton–Raphson iteration.

| Component | Energy | MNA Treatment |
|---|---|---|
| [Resistor](resistor.md) | Dissipates | Conductance stamp (`G = 1/R`) |
| [Capacitor](capacitor.md) | Stores (electric field) | Companion model (equiv. conductance + history current) |
| [Inductor](inductor.md) | Stores (magnetic field) | Companion model (equiv. conductance + history current) |

## Import

```python
from PyEEL import Resistor, Capacitor, Inductor
```

## Common Pattern

```python
ckt.AddComponent(Resistor("R1", (n1, n2), resistance=1e3))
ckt.AddComponent(Capacitor("C1", (n1, gnd), capacitance=100e-6))
ckt.AddComponent(Inductor("L1", (n1, n2), inductance=10e-3))
```
