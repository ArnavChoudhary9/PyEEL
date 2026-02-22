# Inductor

An ideal linear inductor: $V = L \dfrac{dI}{dt}$.

```python
from PyEEL import Inductor

ckt.AddComponent(Inductor("L1", (n1, n2), inductance=10e-3))
```

## Constructor

```python
Inductor(name: str, nodes: tuple[Node, Node], inductance: float)
```

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | Unique component name |
| `nodes` | `(Node, Node)` | `(positive, negative)` terminals |
| `inductance` | `float` | Inductance in **Henries (H)**. Must be > 0. |

## Properties

| Property | Type | Description |
|---|---|---|
| `Inductance` | `float` | The inductance value in H |

## MNA Stamp — Backward Euler Companion

The inductor uses a companion model similar to the capacitor but with
inverted roles:

$$
V_n = \frac{L}{\Delta t} \cdot I_n - \frac{L}{\Delta t} \cdot I_{n-1}
$$

Rearranged into a conductance form:

- $G_{eq} = \dfrac{\Delta t}{L}$ — equivalent conductance
- $I_{hist} = I_{n-1}$ — stored inductor current from the previous step

The inductor registers one **auxiliary unknown** for its branch current.

## DC Behaviour

In DC operating-point analysis, the inductor becomes a **short circuit**
(implemented as a very small resistance, `dc_inductor_resistance` from
the simulation config — default `1e-9 Ω`).

## Choosing Inductance Values

| Value | Typical Use |
|---|---|
| 1 µH – 100 µH | Switch-mode power supplies, RF |
| 1 mH – 100 mH | Audio crossover, filtering |
| 0.1 H – 10 H | Mains transformers, coupled inductors |
