# Zener Diode

Models a diode with a well-defined **reverse breakdown voltage** used for
voltage regulation and clamping.

```python
from PyEEL import ZenerDiode

ckt.AddComponent(ZenerDiode("DZ1", (n_anode, n_cathode), Vz=5.1))
```

## Constructor

```python
ZenerDiode(name: str, nodes: tuple[Node, Node], *,
           Vz=5.1, Is=1e-14, n=1.0, Ibv=1e-3, n_bv=1.0, Vt=0.02585)
```

| Parameter | Symbol | Default | Description |
|---|---|---|---|
| `name` | — | — | Unique component name |
| `nodes` | — | — | `(anode, cathode)` |
| `Vz` | $V_Z$ | `5.1` | **Zener breakdown voltage** (V). The reverse voltage at which the diode conducts heavily. |
| `Is` | $I_S$ | `1e-14` | **Forward saturation current** (A) — same as standard diode |
| `n` | $n$ | `1.0` | **Forward emission coefficient** |
| `Ibv` | $I_{BV}$ | `1e-3` | **Breakdown current** (A). Current at which the reverse breakdown knee is defined. |
| `n_bv` | $n_{BV}$ | `1.0` | **Breakdown emission coefficient**. Sharpness of the reverse knee. |
| `Vt` | $V_T$ | `0.02585` | **Thermal voltage** at 25 °C |

## Properties

| Property | Type | Description |
|---|---|---|
| `ZenerVoltage` | `float` | $V_Z$ in Volts |
| `SaturationCurrent` | `float` | $I_S$ in Amps |
| `EmissionCoefficient` | `float` | $n$ |
| `ThermalVoltage` | `float` | $V_T$ in Volts |
| `BreakdownCurrent` | `float` | $I_{BV}$ in Amps |

## Device Equation

The Zener diode combines **forward** and **reverse** exponentials:

$$
I = I_S \left( e^{\frac{V_D}{n V_T}} - 1 \right)
  + I_{BV} \left( e^{\frac{-(V_D + V_Z)}{n_{BV} V_T}} - 1 \right)
$$

- **First term** — standard forward Shockley diode (same as `Diode`).
- **Second term** — reverse breakdown: becomes significant when $V_D < -V_Z$.

### Physical Meaning of Parameters

- **$V_Z$ (Zener Voltage):** The reverse voltage at which the diode enters
  breakdown.  Standard values: 2.4 V, 3.3 V, 5.1 V, 6.2 V, 12 V, 15 V.

- **$I_{BV}$ (Breakdown Current):** The knee current — the current at which
  the breakdown transition is referenced.  Larger values make the breakdown
  knee softer.

- **$n_{BV}$ (Breakdown Emission Coefficient):** Controls the sharpness of
  the reverse breakdown transition.  Lower values produce a sharper, more
  ideal Zener knee.

## Typical Applications

| Application | Circuit |
|---|---|
| **Voltage regulation** | Series resistor + Zener to GND → regulated output |
| **Overvoltage clamp** | Zener across sensitive input pins |
| **Waveform clipper** | Zener in series/parallel with signal path |

## Typical Part Values

| Part | $V_Z$ | $I_{BV}$ | Package |
|---|---|---|---|
| BZX55C3V3 | 3.3 V | 5 mA | DO-35, 500 mW |
| BZX55C5V1 | 5.1 V | 5 mA | DO-35, 500 mW |
| BZX55C12 | 12 V | 1 mA | DO-35, 500 mW |

## Example — Shunt Regulator

```python
# 12 V input → 470 Ω series R → 5.1 V Zener → GND
ckt.AddComponent(DCVoltageSource("V1", (n_in, gnd), voltage=12))
ckt.AddComponent(Resistor("Rs", (n_in, n_out), resistance=470))
ckt.AddComponent(ZenerDiode("DZ1", (gnd, n_out), Vz=5.1))
ckt.AddComponent(Resistor("RL", (n_out, gnd), resistance=2000))
# V_out ≈ 5.1 V
```

> Note the Zener orientation: `(anode=GND, cathode=n_out)` so it conducts
> in reverse from `n_out` to GND when `V(n_out) > Vz`.
