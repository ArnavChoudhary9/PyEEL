# Mutual Coupling

Couples two `Inductor` components magnetically, modelling the shared
magnetic flux.

```python
from PyEEL import Inductor, MutualCoupling

L1 = Inductor("L1", (n1, n2), inductance=10e-3)
L2 = Inductor("L2", (n3, n4), inductance=10e-3)
K1 = MutualCoupling("K1", L1, L2, k=0.8)

ckt.AddComponent(L1)
ckt.AddComponent(L2)
ckt.AddComponent(K1)
```

## Constructor

```python
MutualCoupling(name: str, inductor1: Inductor, inductor2: Inductor, k: float)
```

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | Unique component name |
| `inductor1` | `Inductor` | First coupled inductor |
| `inductor2` | `Inductor` | Second coupled inductor |
| `k` | `float` | **Coupling coefficient**, $-1 < k < 1$ (typically 0.9–0.999 for transformers) |

## Properties

| Property | Type | Description |
|---|---|---|
| `CouplingCoefficient` | `float` | $k$ |
| `MutualInductance` | `float` | $M = k\sqrt{L_1 L_2}$ |
| `Inductor1` | `Inductor` | First inductor reference |
| `Inductor2` | `Inductor` | Second inductor reference |

## Methods

| Method | Returns | Description |
|---|---|---|
| `GetInductorCurrents(solution)` | `(float, float)` | Currents through both inductors |

## Physics

The mutual inductance is:

$$
M = k \sqrt{L_1 L_2}
$$

where $k$ is the coupling coefficient:
- $k = 1$ — perfect coupling (not allowed numerically; use 0.999)
- $k = 0$ — no coupling (independent inductors)
- $k < 0$ — inverted coupling (dot convention flip)

The coupled inductor equations:

$$
V_1 = L_1 \frac{dI_1}{dt} + M \frac{dI_2}{dt}
$$

$$
V_2 = M \frac{dI_1}{dt} + L_2 \frac{dI_2}{dt}
$$

## MNA Stamp

In Backward Euler, the coupling adds cross-terms between the two inductor
companion models — an equivalent cross-conductance proportional to $M/\Delta t$.

## DC Behaviour

In DC, the mutual coupling (like inductors themselves) becomes a short
circuit.  No cross-coupling terms are stamped.

> **Tip:** For most transformer applications, use the higher-level
> [`Transformer`](transformer.md) class which wraps two inductors and a
> mutual coupling into a single object.
