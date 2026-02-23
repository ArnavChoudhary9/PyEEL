# Op-Amp (Operational Amplifier)

> **Module:** `PyEEL.Components.ICs.OpAmp`
>
> **Import:** `from PyEEL import OpAmp`  or
> `from PyEEL.Components.ICs import OpAmp`

## Overview

The `OpAmp` class implements a **voltage-feedback macro model** of an
operational amplifier.  It is suitable for both DC and transient analysis of circuits that use negative feedback (or, with saturation enabled, open-loop circuits).

Three levels of fidelity are available:

| Level | Configuration | `IsNonlinear` |
|---|---|---|
| **Ideal** | `A_OL=1e9, R_in=1e12, R_out=0.001` | `False` |
| **Linear** | Finite gain / impedance (default LM741-like) | `False` |
| **Saturating** | Same + output voltage clamping | `True` |

## Terminal Convention

```
nodes = (non_inverting_input, inverting_input, output)
         V+                   V-                Vout
```

The output is **single-ended**, referenced to ground.

## Constructor

```python
OpAmp(name, nodes, *,
      A_OL=200_000.0,
      R_in=2e6,
      R_out=75.0,
      V_sat_pos=None,
      V_sat_neg=None)
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | — | Component identifier (e.g. `'U1'`) |
| `nodes` | `tuple[Node, Node, Node]` | — | `(V+, V-, Vout)` |
| `A_OL` | `float` | `200_000` | Open-loop DC voltage gain (~106 dB) |
| `R_in` | `float` | `2e6` | Differential input resistance (Ω) |
| `R_out` | `float` | `75.0` | Output resistance (Ω) |
| `V_sat_pos` | `float \| None` | `None` | Positive output saturation voltage |
| `V_sat_neg` | `float \| None` | `None` | Negative saturation (defaults to `-V_sat_pos`) |

### Physical meaning of each parameter

- **`A_OL`** — Open-loop voltage gain.  This is the gain with no
  external feedback network.  Real op-amps have 100–120 dB
  ($10^5$ – $10^6$).  With negative feedback the closed-loop gain is
  determined by external resistors, not `A_OL`.

- **`R_in`** — Differential input resistance between V+ and V-.
  Bipolar op-amps (LM741): ~2 MΩ.  FET-input (TL072): ~$10^{12}$ Ω.
  Determines how much current the input draws from the signal source.

- **`R_out`** — Open-loop output resistance.  With negative feedback
  the effective output impedance drops to
  $R_{out,eff} \approx R_{out} / (1 + A_{OL} \cdot \beta)$
  where $\beta$ is the feedback fraction.

- **`V_sat_pos / V_sat_neg`** — Output voltage limits, typically
  ~1–2 V below the supply rails.  When the open-loop output
  $A_{OL} \cdot (V^+ - V^-)$ would exceed these limits, the model
  clamps the output and the gain drops to zero (saturation).  Leave
  `None` for a purely linear model.

## MNA Model

The op-amp uses **one auxiliary unknown** — the output branch
current $I_{out}$.

### Internal equivalent circuit

```
           G_in = 1/R_in
  V+ ──┬──/\/\/──┬── V-
       │         │
       │    ┌────┘
       │    │
       │  ╔═══════════════╗
       │  ║  Controlled   ║
       │  ║  Voltage Src  ║  V = A_OL · (V+ - V-)
       │  ╚═══════╤═══════╝
       │          │
       │         R_out
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

**Output stage** (auxiliary row for KVL, plus KCL at output):

$$V_{out} - R_{out} \cdot I_{aux} - A_{OL} \cdot (V^+ - V^-) = 0$$

$$
\begin{aligned}
A[\text{aux}, V_{out}] &+= 1 \\
A[\text{aux}, \text{aux}] &-= R_{out} \\
A[\text{aux}, V^+] &-= A_{OL} \\
A[\text{aux}, V^-] &+= A_{OL} \\
A[V_{out}, \text{aux}] &+= 1 & \text{(KCL)}
\end{aligned}
$$

### Saturation (piecewise-linear)

When saturation is enabled, the Stamp method checks the current
operating point at each Newton–Raphson iteration:

- **Linear region** ($V_{sat,neg} < A_{OL} \cdot V_{diff} < V_{sat,pos}$):
  normal stamp above.
- **Positive saturation** ($A_{OL} \cdot V_{diff} > V_{sat,pos}$):
  replaces the VCVS equation with $V_{out} - R_{out} \cdot I_{aux} = V_{sat,pos}$.
- **Negative saturation** ($A_{OL} \cdot V_{diff} < V_{sat,neg}$):
  replaces with $V_{out} - R_{out} \cdot I_{aux} = V_{sat,neg}$.

## Properties

| Property | Returns | Description |
|---|---|---|
| `OpenLoopGain` | `float` | $A_{OL}$ |
| `InputResistance` | `float` | $R_{in}$ (Ω) |
| `OutputResistance` | `float` | $R_{out}$ (Ω) |
| `SaturationPositive` | `float \| None` | $V_{sat,pos}$ |
| `SaturationNegative` | `float \| None` | $V_{sat,neg}$ |
| `IsNonlinear` | `bool` | `True` when saturation is enabled |

## Query Methods

| Method | Returns | Description |
|---|---|---|
| `GetVoltage(sv)` | `float` | Output voltage $V_{out}$ |
| `GetCurrent(sv)` | `float` | Output branch current $I_{out}$ |
| `GetDifferentialInput(sv)` | `float` | $V^+ - V^-$ |

## Example: Inverting Amplifier

```python
from PyEEL import (Circuit, NodeManager, OpAmp, Resistor,
                   DCVoltageSource, NumpySolver, SimulationConfig,
                   VoltageProbe)

nm  = NodeManager()
gnd = nm.GroundNode
n_in  = nm.AddNode("in")
n_inv = nm.AddNode("inv")
n_out = nm.AddNode("out")

config = SimulationConfig(dt=1e-4, t_end=0.01)
ckt = Circuit(solver=NumpySolver(), config=config, nodeManager=nm)

# DC input
ckt.AddComponent(DCVoltageSource("Vin", (n_in, gnd), voltage=1.0))

# Inverting amplifier: gain = -Rf/Rin = -100k/10k = -10
ckt.AddComponent(Resistor("Rin", (n_in, n_inv), resistance=10e3))
ckt.AddComponent(Resistor("Rf",  (n_inv, n_out), resistance=100e3))
ckt.AddComponent(OpAmp("U1", (gnd, n_inv, n_out)))

# Load resistor (prevents floating output)
ckt.AddComponent(Resistor("Rload", (n_out, gnd), resistance=10e3))

p = VoltageProbe("Vout", n_out, gnd)
ckt.AddProbe(p)
ckt.Finalize()
ckt.RunDC()

print(f"Vout = {p.Data[-1]:.2f} V")   # ≈ -10.0 V
```

## Example: Non-Inverting Amplifier with Saturation

```python
ckt.AddComponent(
    OpAmp("U1", (n_in, n_fb, n_out),
          A_OL=200_000, R_in=2e6, R_out=75.0,
          V_sat_pos=13.0, V_sat_neg=-13.0)
)
```

This clips the output at ±13 V (typical for a ±15 V supply with
~2 V dropout).

## Pre-Built Library Parts

See [Component Library — Op-Amps](../library/overview.md) for
ready-to-use factory functions like `LM741`, `TL072`, `NE5532`, etc.

## Common Topologies

See [Common Building Blocks](../library/common.md) for factory helpers:
`inverting_amplifier`, `non_inverting_amplifier`, `voltage_follower`,
`summing_amplifier`, `difference_amplifier`, `integrator`,
`differentiator`.

## Tips

- Always include a **load resistor** on the output to avoid a floating
  node.  Even 10 kΩ to ground is sufficient.
- For DC-only analysis, disable transient mode:
  `SimulationConfig(dt=1e-4, t_end=0.01, mode=SimulationMode.DC_ONLY)`.
- The default parameters match a typical **LM741**.  Use the library
  for other parts.
- For an "ideal" op-amp, use `IdealOpAmp` from the library, or set
  `A_OL=1e9, R_in=1e12, R_out=0.001`.
