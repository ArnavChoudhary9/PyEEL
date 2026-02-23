# Transformer

A high-level wrapper that creates two coupled inductors and a
`MutualCoupling` in a single object.  Models an ideal (or near-ideal)
transformer.

```python
from PyEEL import Transformer

T1 = Transformer("T1",
    primary_nodes=(n_pri_p, n_pri_n),
    secondary_nodes=(n_sec_p, n_sec_n),
    primary_inductance=100.0,
    secondary_inductance=0.25,
    k=0.999,
)
ckt.AddComponent(T1)
```

## Constructor

```python
Transformer(name: str,
            primary_nodes: tuple[Node, Node],
            secondary_nodes: tuple[Node, Node],
            primary_inductance: float,
            secondary_inductance: float,
            k: float)
```

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | Unique component name |
| `primary_nodes` | `(Node, Node)` | `(p+, p-)` of the primary winding |
| `secondary_nodes` | `(Node, Node)` | `(s+, s-)` of the secondary winding |
| `primary_inductance` | `float` | $L_1$ in **Henries** |
| `secondary_inductance` | `float` | $L_2$ in **Henries** |
| `k` | `float` | Coupling coefficient (0 < k < 1; use 0.999 for near-ideal) |

## Properties

| Property | Type | Description |
|---|---|---|
| `Primary` | `Inductor` | The primary winding inductor |
| `Secondary` | `Inductor` | The secondary winding inductor |
| `Coupling` | `MutualCoupling` | The coupling component |
| `TurnsRatio` | `float` | $n = \sqrt{L_1 / L_2}$ |
| `MutualInductance` | `float` | $M = k\sqrt{L_1 L_2}$ |
| `CouplingCoefficient` | `float` | $k$ |

## Methods

| Method | Returns | Description |
|---|---|---|
| `GetCurrent(solution)` | `float` | Primary winding current |
| `GetVoltage(solution)` | `float` | Primary winding voltage |
| `GetSecondaryCurrent(solution)` | `float` | Secondary winding current |
| `GetSecondaryVoltage(solution)` | `float` | Secondary winding voltage |

## Turns Ratio and Inductance

For an ideal transformer with turns ratio $n = N_1/N_2$:

$$
\frac{V_1}{V_2} = n, \qquad \frac{I_2}{I_1} = n
$$

The relationship between inductances and turns ratio:

$$
n = \frac{N_1}{N_2} = \sqrt{\frac{L_1}{L_2}}
$$

So to model a step-down transformer from $V_1$ to $V_2$:

$$
L_2 = L_1 \cdot \left(\frac{V_2}{V_1}\right)^2
$$

### Example: 240 V → 12 V

With $L_1 = 100$ H:

$$
L_2 = 100 \times \left(\frac{12}{240}\right)^2 = 100 \times 0.0025 = 0.25 \text{ H}
$$

## Using Current Probes

To measure the current through a transformer winding, pass the internal
inductor to a `CurrentProbe`:

```python
ckt.AddProbe(CurrentProbe("I_pri", T1.Primary))
ckt.AddProbe(CurrentProbe("I_sec", T1.Secondary))
```

## Example — Step-Down Transformer with Load

```python
n_pri = nm.AddNode("pri")
n_sec = nm.AddNode("sec")

ckt.AddComponent(ACVoltageSource("Vmains", (n_pri, gnd),
                                  amplitude=339.4, frequency=50))
T1 = Transformer("T1", (n_pri, gnd), (n_sec, gnd),
                 primary_inductance=100.0,
                 secondary_inductance=0.25,
                 k=0.999)
ckt.AddComponent(T1)
ckt.AddComponent(Resistor("RL", (n_sec, gnd), resistance=100))
# V_sec ≈ 339.4 / 20 ≈ 17 V peak (≈ 12 V RMS)
```
