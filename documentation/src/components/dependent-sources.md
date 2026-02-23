# Dependent Sources (VCVS, VCCS, CCVS, CCCS)

Dependent (controlled) sources produce an output that is proportional to a
voltage or current elsewhere in the circuit.  They are used to model
amplifiers, transconductance stages, and feedback networks.

```python
from PyEEL import VCVS, VCCS, CCVS, CCCS
```

## Overview

| Class | SPICE Name | Relation | Control | Output |
|---|---|---|---|---|
| `VCVS` | E | $V_{out} = A_v \cdot V_{ctrl}$ | Voltage | Voltage |
| `VCCS` | G | $I_{out} = g_m \cdot V_{ctrl}$ | Voltage | Current |
| `CCVS` | H | $V_{out} = R_m \cdot I_{ctrl}$ | Current | Voltage |
| `CCCS` | F | $I_{out} = A_i \cdot I_{ctrl}$ | Current | Current |

## VCVS — Voltage-Controlled Voltage Source

```python
VCVS(name: str, out_nodes: tuple[Node, Node],
     ctrl_nodes: tuple[Node, Node], gain: float)
```

| Parameter | Symbol | Description |
|---|---|---|
| `out_nodes` | — | `(out+, out-)` where the controlled voltage appears |
| `ctrl_nodes` | — | `(ctrl+, ctrl-)` the sensed voltage |
| `gain` | $A_v$ | **Voltage gain** (V/V) — dimensionless |

**Auxiliary unknowns:** 1 (output branch current)

**Equation:** $V_{out+} - V_{out-} = A_v \cdot (V_{ctrl+} - V_{ctrl-})$

## VCCS — Voltage-Controlled Current Source

```python
VCCS(name: str, out_nodes: tuple[Node, Node],
     ctrl_nodes: tuple[Node, Node], transconductance: float)
```

| Parameter | Symbol | Description |
|---|---|---|
| `out_nodes` | — | `(out+, out-)` current flows from out+ to out- |
| `ctrl_nodes` | — | `(ctrl+, ctrl-)` the sensed voltage |
| `transconductance` | $g_m$ | **Transconductance** (A/V) — Siemens |

**Auxiliary unknowns:** 0

**Equation:** $I_{out} = g_m \cdot (V_{ctrl+} - V_{ctrl-})$

## CCVS — Current-Controlled Voltage Source

```python
CCVS(name: str, out_nodes: tuple[Node, Node],
     ctrl_nodes: tuple[Node, Node], transresistance: float)
```

| Parameter | Symbol | Description |
|---|---|---|
| `out_nodes` | — | `(out+, out-)` where the controlled voltage appears |
| `ctrl_nodes` | — | `(ctrl+, ctrl-)` a **zero-volt sense source** is inserted here |
| `transresistance` | $R_m$ | **Transresistance** (V/A) — Ohms |

**Auxiliary unknowns:** 2 (sense branch current + output branch current)

**Equation:** $V_{out} = R_m \cdot I_{sense}$

> The CCVS inserts a zero-volt voltage source across `ctrl_nodes` to
> measure the control current.  This is the same technique used in SPICE.

## CCCS — Current-Controlled Current Source

```python
CCCS(name: str, out_nodes: tuple[Node, Node],
     ctrl_nodes: tuple[Node, Node], gain: float)
```

| Parameter | Symbol | Description |
|---|---|---|
| `out_nodes` | — | `(out+, out-)` current flows from out+ to out- |
| `ctrl_nodes` | — | `(ctrl+, ctrl-)` a **zero-volt sense source** is inserted here |
| `gain` | $A_i$ | **Current gain** (A/A) — dimensionless |

**Auxiliary unknowns:** 1 (sense branch current)

**Equation:** $I_{out} = A_i \cdot I_{sense}$

## Query Methods

All dependent sources provide:

| Method | Returns |
|---|---|
| `GetCurrent(solution)` | Output branch current |
| `GetVoltage(solution)` | Output voltage |

Current-controlled sources also provide:

| Method | Returns |
|---|---|
| `GetSenseCurrent(solution)` | Current through the zero-volt sense source |

## Example — VCVS (Gain of 3)

```python
n_in  = nm.AddNode("in")
n_out = nm.AddNode("out")

ckt.AddComponent(ACVoltageSource("Vin", (n_in, gnd), amplitude=1, frequency=100))
ckt.AddComponent(VCVS("E1", (n_out, gnd), (n_in, gnd), gain=3.0))
ckt.AddComponent(Resistor("RL", (n_out, gnd), resistance=1e3))
# V_out = 3 × V_in → 3 V peak
```

## Example — VCCS (Transconductance Amplifier)

```python
ckt.AddComponent(VCCS("G1", (n_out, gnd), (n_in, gnd), transconductance=2e-3))
ckt.AddComponent(Resistor("RL", (n_out, gnd), resistance=2e3))
# V_out = gm × V_in × RL = 2e-3 × 1 × 2e3 = 4 V peak
```
