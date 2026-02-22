# Diode

Models a semiconductor diode using the **Shockley diode equation**.

```python
from PyEEL import Diode

ckt.AddComponent(Diode("D1", (n_anode, n_cathode), Is=1e-14, n=1.0))
```

## Constructor

```python
Diode(name: str, nodes: tuple[Node, Node], *, Is=1e-14, n=1.0, Vt=0.02585)
```

| Parameter | Symbol | Default | Description |
|---|---|---|---|
| `name` | — | — | Unique component name |
| `nodes` | — | — | `(anode, cathode)` |
| `Is` | $I_S$ | `1e-14` | **Saturation current** (A). Reverse-bias leakage. Larger values → lower forward voltage. |
| `n` | $n$ | `1.0` | **Emission coefficient** (ideality factor). 1.0 = ideal; real diodes 1.0–2.0. |
| `Vt` | $V_T$ | `0.02585` | **Thermal voltage** $\frac{kT}{q}$ at 25 °C (≈ 25.85 mV) |

## Properties

| Property | Type | Description |
|---|---|---|
| `SaturationCurrent` | `float` | $I_S$ in Amps |
| `EmissionCoefficient` | `float` | $n$ (dimensionless) |
| `ThermalVoltage` | `float` | $V_T$ in Volts |

## The Shockley Equation

$$
I_D = I_S \left( e^{\frac{V_D}{n V_T}} - 1 \right)
$$

where $V_D = V_{anode} - V_{cathode}$.

### Physical Meaning of Parameters

- **$I_S$ (Saturation Current):** The tiny reverse-bias current that flows
  due to minority carriers.  Typical values range from `1e-15` (small-signal)
  to `1e-5` (Schottky).  Doubling $I_S$ reduces the forward voltage by
  about $n V_T \ln 2 \approx 18$ mV.

- **$n$ (Emission Coefficient):** Models recombination in the depletion
  region.  $n = 1$ for an ideal diode; $n \approx 1.7$–$2.0$ for
  real silicon diodes.  LEDs have higher $n$ values (1.8–2.1).

- **$V_T$ (Thermal Voltage):** $kT/q$ — about 25.85 mV at room temperature
  (25 °C).  Changes with temperature: $V_T = T/11{,}586$ (T in Kelvin).

## SPICE-Style Voltage Limiting

To prevent numerical overflow in $e^{V_D/(nV_T)}$, PyEEL implements
SPICE-style voltage limiting: the diode voltage change per Newton–Raphson
iteration is clamped, and the exponential argument is capped at a safe
maximum.

## N-R Linearisation

At operating point $V_0$:

- Conductance: $g_d = \dfrac{I_S}{n V_T} \cdot e^{V_0/(nV_T)}$
- Current source: $I_{eq} = I_D(V_0) - g_d \cdot V_0$

## DC Behaviour

The diode is nonlinear in both DC and transient.  The DC operating-point
solver finds the bias using Newton–Raphson (with source-stepping and
gmin-stepping fallbacks).

## Typical Part Values

| Part | $I_S$ | $n$ | Application |
|---|---|---|---|
| 1N4007 (rectifier) | `7.02e-9` | `1.77` | Power rectification |
| 1N4148 (signal) | `2.52e-9` | `1.75` | Fast switching |
| 1N5819 (Schottky) | `2.5e-5` | `1.05` | Low-drop rectifier |
| Red LED | `1.2e-20` | `1.8` | Indicator ($V_f \approx 1.8$ V) |

> **Tip:** Use functions from `PyEEL.Components.library` for real-world
> parts with datasheet values pre-filled. See
> [Component Library](../library/overview.md).
