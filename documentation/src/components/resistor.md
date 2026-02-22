# Resistor

An ideal linear resistor that obeys Ohm's Law: $V = IR$.

```python
from PyEEL import Resistor

ckt.AddComponent(Resistor("R1", (n1, n2), resistance=1000))
```

## Constructor

```python
Resistor(name: str, nodes: tuple[Node, Node], resistance: float)
```

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | Unique component name |
| `nodes` | `(Node, Node)` | `(positive, negative)` terminals |
| `resistance` | `float` | Resistance in **Ohms (Ω)**. Must be > 0. |

## Properties

| Property | Type | Description |
|---|---|---|
| `Resistance` | `float` | The resistance value in Ω |

## MNA Stamp

The resistor stamps a **conductance** $G = 1/R$ into the MNA matrix:

$$
\begin{bmatrix} +G & -G \\ -G & +G \end{bmatrix}
$$

applied to rows/columns corresponding to the two terminal nodes.  If either
node is ground, that row/column is simply omitted.

## DC Behaviour

Resistors behave identically in DC and transient analysis.

## Example — Voltage Divider

```python
n_in  = nm.AddNode("in")
n_out = nm.AddNode("out")

ckt.AddComponent(DCVoltageSource("V1", (n_in, gnd), voltage=10))
ckt.AddComponent(Resistor("R1", (n_in, n_out), resistance=1000))
ckt.AddComponent(Resistor("R2", (n_out, gnd), resistance=1000))
# V_out = 10 × 1000/(1000+1000) = 5 V
```
