# Capacitor

An ideal linear capacitor: $I = C \dfrac{dV}{dt}$.

```python
from PyEEL import Capacitor

ckt.AddComponent(Capacitor("C1", (n1, gnd), capacitance=100e-6))
```

## Constructor

```python
Capacitor(name: str, nodes: tuple[Node, Node], capacitance: float)
```

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | Unique component name |
| `nodes` | `(Node, Node)` | `(positive, negative)` terminals |
| `capacitance` | `float` | Capacitance in **Farads (F)**. Must be > 0. |

## Properties

| Property | Type | Description |
|---|---|---|
| `Capacitance` | `float` | The capacitance value in F |

## MNA Stamp — Backward Euler Companion

During transient analysis the capacitor is replaced by an equivalent
**companion model** using the Backward Euler approximation:

$$
I_n = G_{eq} \cdot V_n - I_{hist}
$$

where:

- $G_{eq} = \dfrac{C}{\Delta t}$ — equivalent conductance
- $I_{hist} = G_{eq} \cdot V_{n-1}$ — history current from the previous time step

This stamps as a conductance $G_{eq}$ plus a current source $I_{hist}$
into the RHS vector.

## DC Behaviour

In DC operating-point analysis ($\Delta t \to \infty$), the capacitor
becomes an **open circuit** — no stamp is applied.

## Choosing Capacitance Values

| Value | Typical Use |
|---|---|
| 100 pF – 1 nF | High-frequency bypass, RF |
| 10 nF – 100 nF | Decoupling (0.1 µF is the universal bypass cap) |
| 1 µF – 100 µF | Signal coupling, timing circuits |
| 100 µF – 1000 µF | Power supply filtering |
