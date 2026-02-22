# Semiconductor Components

Semiconductor devices exhibit **non-linear** I–V characteristics, meaning
the MNA system cannot be solved in a single step.  PyEEL uses
**Newton–Raphson iteration** to linearise these devices around the current
operating point at each time step.

| Component | Model | Terminals |
|---|---|---|
| [Diode](diode.md) | Shockley equation | anode, cathode |
| [Zener Diode](zener-diode.md) | Forward Shockley + reverse breakdown | anode, cathode |
| [BJT](bjt.md) | Ebers–Moll (+ Early effect) | collector, base, emitter |
| [MOSFET](mosfet.md) | Level-1 Shichman–Hodges | drain, gate, source |

All semiconductor components set `IsNonlinear = True`, which triggers the
Newton–Raphson solver.

## Import

```python
from PyEEL import Diode, ZenerDiode, BJT, BJTType, NPN, PNP, MOSFET, MOSFETType, NMOS, PMOS
```

## Linearisation (How N-R Works)

At each Newton–Raphson iteration the non-linear device:

1. **Reads** the current approximate voltages from `context.x_current`.
2. **Evaluates** the device equations at that operating point.
3. **Stamps** a linearised conductance + current source into the MNA matrix.
4. The solver finds a better solution; repeat until convergence.

The stamp at each iteration consists of:

- A **differential conductance** $g = \dfrac{\partial I}{\partial V}$ (goes into `A`)
- An **equivalent current source** $I_{eq} = I(V_0) - g \cdot V_0$ (goes into `b`)

This is the standard **companion model** approach used in SPICE-class
simulators.
