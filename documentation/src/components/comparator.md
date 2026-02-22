# Comparator

> **Module:** `PyEEL.Components.ICs.Comparator`
>
> **Import:** `from PyEEL import Comparator`  or
> `from PyEEL.Components.ICs import Comparator`

## Overview

The `Comparator` class implements a **rail-to-rail output comparator macro model**.
It compares two input voltages and drives its output to a defined high or low voltage
level, optionally with **hysteresis** (Schmitt-trigger behaviour).

| Level | Configuration | `IsNonlinear` |
|---|---|---|
| **Ideal** | `R_in=1e12, R_out=0.001` (IdealComparator) | `True` |
| **Standard** | Finite input/output impedance (default LM393-like) | `True` |
| **With hysteresis** | `V_hys > 0` adds dead-band to prevent chatter | `True` |

> Unlike an op-amp in feedback, a comparator always operates
> **open-loop** — the output switches discretely between two rails.

## Terminal Convention

```
nodes = (non_inverting_input, inverting_input, output)
         V+                   V-                Vout
```

The output is **single-ended**, referenced to ground.

## Constructor

```python
Comparator(name, nodes, *,
           V_high=5.0,
           V_low=0.0,
           V_hys=0.0,
           R_in=1e6,
           R_out=50.0,
           initial_state_high=True)
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | — | Component identifier (e.g. `'U1'`) |
| `nodes` | `tuple[Node, Node, Node]` | — | `(V+, V-, Vout)` |
| `V_high` | `float` | `5.0` | Output high voltage (V) |
| `V_low` | `float` | `0.0` | Output low voltage (V) |
| `V_hys` | `float` | `0.0` | Total hysteresis band width (V); trip points at ±V_hys/2 |
| `R_in` | `float` | `1e6` | Differential input resistance (Ω) |
| `R_out` | `float` | `50.0` | Output resistance (Ω) |
| `initial_state_high` | `bool` | `True` | Starting output state before first NR iteration |

### Physical meaning of each parameter

- **`V_high / V_low`** — Output voltage rails.  For a 5 V supply, typical
  values are `V_high=5.0, V_low=0.0`.  For a ±15 V supply you might use
  `V_high=14.0, V_low=-14.0`.

- **`V_hys`** — Total hysteresis window.  When `V_hys=1.0`, the output
  transitions to HIGH when `V+ − V− > 0.5 V`, and to LOW when
  `V+ − V− < −0.5 V`.  Within the band the previous state is held.
  Setting `V_hys=0` gives a zero-hysteresis ideal comparator.

- **`R_in`** — Differential input resistance between V+ and V-.  Typical
  values: LM393 ~1 MΩ, CMOS comparators ~1 TΩ.

- **`R_out`** — Output resistance (push-pull model).  Many real
  comparators have open-collector outputs — model these by adding an
  external pull-up resistor and setting `R_out` to a small value.

- **`initial_state_high`** — Sets which output rail is assumed at
  time zero before the solver has evaluated the input voltages.  This
  only affects the first Newton–Raphson iteration; the solver converges
  to the correct state regardless.

## MNA Model

The comparator uses **one auxiliary unknown** — the output branch
current $I_{aux}$.

### Internal equivalent circuit

```
           G_in = 1/R_in
  V+ ──┬──/\/\/──┬── V−
       │         │
       │  ┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐
       │  ╎  Piecewise output: V_target ∈ {V_high, V_low} ╎
       │  └╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘
       │          │ R_out
       │          │
       └──────── Vout
```

### Stamp equations

**Input resistance** (conductance $G = 1/R_{in}$):

$$
\begin{aligned}
A[V^+, V^+] &+= G \\
A[V^+, V^-] &-= G \\
A[V^-, V^-] &+= G \\
A[V^-, V^+] &-= G
\end{aligned}
$$

**Output stage** (KCL at output, KVL auxiliary row):

$$V_{out} - R_{out} \cdot I_{aux} = V_{target}$$

where $V_{target} \in \{V_{high},\, V_{low}\}$ is chosen based on the
current Newton–Raphson iterate.

$$
\begin{aligned}
A[V_{out}, I_{aux}] &+= 1 & \text{(KCL)} \\
A[\text{aux}, V_{out}] &+= 1 \\
A[\text{aux}, I_{aux}] &-= R_{out} \\
b[\text{aux}] &+= V_{target}
\end{aligned}
$$

### Hysteresis logic

At each NR iteration, the differential voltage is computed from the
current solution vector $x$:

$$\Delta V = x[V^+] - x[V^-]$$

State transitions:

$$
\text{state} = \begin{cases}
\text{HIGH} & \Delta V > +V_{hys}/2 \\
\text{LOW}  & \Delta V < -V_{hys}/2 \\
\text{hold previous} & \text{otherwise (dead-band)}
\end{cases}
$$

## Properties

| Property | Returns | Description |
|---|---|---|
| `OutputHigh` | `float` | Configured `V_high` |
| `OutputLow` | `float` | Configured `V_low` |
| `Hysteresis` | `float` | `V_hys` (total dead-band width) |
| `InputResistance` | `float` | $R_{in}$ (Ω) |
| `OutputResistance` | `float` | $R_{out}$ (Ω) |
| `IsStateHigh` | `bool` | `True` when output is currently in HIGH state |
| `IsNonlinear` | `bool` | Always `True` |

## Query Methods

| Method | Returns | Description |
|---|---|---|
| `GetVoltage(sv)` | `float` | Output voltage $V_{out}$ |
| `GetCurrent(sv)` | `float` | Output branch current $I_{aux}$ |
| `GetDifferentialInput(sv)` | `float` | $V^+ - V^-$ |

## Example: Simple Voltage Comparator

```python
from PyEEL import (Circuit, Comparator, DCVoltageSource, Resistor,
                   NumpySolver, VoltageProbe)
from PyEEL.SimulationContext import SimulationConfig

config = SimulationConfig(dc_operating_point=True)
ckt = Circuit(solver=NumpySolver(), config=config)
nm  = ckt.NodeManager
gnd = nm.GroundNode

n_in  = nm.AddNode("in")
n_ref = nm.AddNode("ref")
n_out = nm.AddNode("out")

# V_in = 3 V, V_ref = 1 V  →  V_out = V_high (5 V)
ckt.AddComponent(DCVoltageSource("Vin",  (n_in,  gnd), voltage=3.0))
ckt.AddComponent(DCVoltageSource("Vref", (n_ref, gnd), voltage=1.0))
ckt.AddComponent(Comparator("U1", (n_in, n_ref, n_out), V_high=5.0, V_low=0.0))
ckt.AddComponent(Resistor("Rload", (n_out, gnd), resistance=10e3))

p = VoltageProbe("Vout", n_out)
ckt.AddProbe(p)
ckt.Finalize()
x = ckt.SolveDCOperatingPoint()

print(f"Vout = {x[n_out.Index]:.2f} V")   # → 5.00 V
```

## Example: Schmitt Trigger with Hysteresis

```python
ckt.AddComponent(
    Comparator("U1", (n_in, n_ref, n_out),
               V_high=5.0, V_low=0.0,
               V_hys=1.0)   # ±0.5 V trip-point spread
)
```

With `V_hys=1.0`: output goes HIGH when `V_in − V_ref > +0.5 V`,
LOW when `V_in − V_ref < −0.5 V`.

## Pre-Built Library Parts

See [Component Library](../library/overview.md) for ready-to-use factory
functions:

| Function | Part | $V_{high}$ | $R_{in}$ | $R_{out}$ | Notes |
|---|---|---|---|---|---|
| `LM393` | LM393 | 5 V | 1 MΩ | 50 Ω | Dual, general purpose |
| `LM339` | LM339 | 5 V | 1 MΩ | 50 Ω | Quad, single supply |
| `LM311` | LM311 | 5 V | 500 kΩ | 50 Ω | Faster, output transistor |
| `TLV3201` | TLV3201 | 5 V | 100 MΩ | 25 Ω | Rail-to-rail CMOS |
| `MAX9021` | MAX9021 | 5 V | 1 TΩ | 10 Ω | Ultra-low power |
| `IdealComparator` | — | 5 V | 1 TΩ | 0.001 Ω | Textbook ideal |

## Common Topologies

See [Common Building Blocks](../library/common.md) for factory helpers:

- **`voltage_comparator`** — single comparator with configurable rails
- **`schmitt_trigger`** — non-inverting Schmitt trigger with resistor feedback
- **`window_comparator`** — two comparators detect if signal is within
  a voltage window

## Tips

- Always add a **pull-up resistor** (e.g. 10 kΩ to `V_supply`) or a **load
  resistor** to ground on the output — leaving the output node unloaded
  will cause a floating node error.
- For open-collector comparators (LM393, LM339): add a pull-up resistor
  to the supply and set `R_out` to a small value (e.g. `5.0`).
- Use `initial_state_high=False` when `V_in < V_ref` at t=0 to avoid an
  extra NR iteration to resolve the initial state.
- For 5 V CMOS logic levels use `V_high=5.0, V_low=0.0`.
  For ±15 V supply use `V_high=14.0, V_low=-14.0` (2 V dropout).
