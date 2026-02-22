# BJT (Bipolar Junction Transistor)

Models NPN and PNP transistors using the **Ebers–Moll** large-signal model
with optional **Early effect** (base-width modulation).

```python
from PyEEL import BJT, BJTType, NPN, PNP

# Full constructor
ckt.AddComponent(BJT("Q1", (n_c, n_b, n_e), BJTType.NPN, Is=14.34e-15, BF=255.9))

# Convenience factories
ckt.AddComponent(NPN("Q1", (n_c, n_b, n_e), BF=200))
ckt.AddComponent(PNP("Q2", (n_c, n_b, n_e), BF=180))
```

## Constructor

```python
BJT(name: str, nodes: tuple[Node, Node, Node], bjt_type=BJTType.NPN, *,
    Is=1e-15, BF=100.0, BR=1.0, Nf=1.0, Nr=1.0, Vt=0.02585, Vaf=None)
```

| Parameter | Symbol | Default | Description |
|---|---|---|---|
| `name` | — | — | Unique component name |
| `nodes` | — | — | `(collector, base, emitter)` |
| `bjt_type` | — | `NPN` | `BJTType.NPN` or `BJTType.PNP` |
| `Is` | $I_S$ | `1e-15` | **Transport saturation current** (A). Controls the overall I–V scale. |
| `BF` | $\beta_F$ | `100.0` | **Forward current gain** ($h_{FE}$). Ratio $I_C / I_B$ in forward active. |
| `BR` | $\beta_R$ | `1.0` | **Reverse current gain**. Ratio in reverse active (usually 0.1–10). |
| `Nf` | $N_F$ | `1.0` | **Forward emission coefficient**. Ideality of the B-E junction. |
| `Nr` | $N_R$ | `1.0` | **Reverse emission coefficient**. Ideality of the B-C junction. |
| `Vt` | $V_T$ | `0.02585` | **Thermal voltage** at 25 °C |
| `Vaf` | $V_{AF}$ | `None` | **Forward Early voltage** (V). `None` disables the Early effect. |

## `BJTType` Enum

| Value | Int | Description |
|---|---|---|
| `NPN` | `1` | Current flows C → E; conventional amplifier polarity |
| `PNP` | `-1` | Current flows E → C; voltages/currents are inverted |

## Properties

| Property | Type | Description |
|---|---|---|
| `Type` | `BJTType` | NPN or PNP |
| `SaturationCurrent` | `float` | $I_S$ |
| `ForwardGain` | `float` | $\beta_F$ |
| `ReverseGain` | `float` | $\beta_R$ |

## Query Methods

| Method | Returns |
|---|---|
| `GetCurrent(solution)` | Collector current $I_C$ |
| `GetVoltage(solution)` | $V_{CE}$ |
| `GetBaseCurrent(solution)` | Base current $I_B$ (from last NR iteration) |
| `GetVbe(solution)` | Base-emitter voltage |
| `GetVbc(solution)` | Base-collector voltage |

## The Ebers–Moll Model

The transport form of the Ebers–Moll model computes:

$$
I_F = I_S \left( e^{\frac{V_{BE}}{N_F V_T}} - 1 \right)
$$

$$
I_R = I_S \left( e^{\frac{V_{BC}}{N_R V_T}} - 1 \right)
$$

$$
I_C = I_F - I_R - \frac{I_R}{\beta_R}
$$

$$
I_B = \frac{I_F}{\beta_F} + \frac{I_R}{\beta_R}
$$

$$
I_E = -(I_C + I_B)
$$

### With Early Effect ($V_{AF} \neq$ None)

The forward current is modulated by $V_{CE}$:

$$
I_C = I_F \left(1 + \frac{V_{CE}}{V_{AF}}\right) - I_R - \frac{I_R}{\beta_R}
$$

This models the finite output resistance $r_o \approx V_{AF} / I_C$.

### Physical Meaning of Parameters

- **$I_S$ (Saturation Current):** The leakage current of both junctions (assumed symmetric in the transport model). Typical: `1e-15`–`1e-11` A.

- **$\beta_F$ (Forward Gain):** The DC current gain $h_{FE}$, typically 100–500 for small-signal BJTs, 20–100 for power devices, 1000+ for Darlington pairs.

- **$\beta_R$ (Reverse Gain):** Much lower than $\beta_F$; models the transistor behaviour when operated in reverse (C and E swapped).

- **$N_F$, $N_R$ (Emission Coefficients):** Usually 1.0 for standard BJTs. Darlington pairs may use $N_F \approx 1.5$ since two junctions are in series.

- **$V_{AF}$ (Early Voltage):** Models the slope of the $I_C$ vs $V_{CE}$ curves. Higher values → flatter curves → higher output resistance. Typical: 50–200 V for small-signal, 100+ V for power.

## PNP Transistors

For PNP, all voltages and currents are internally negated by the `BJTType`
polarity factor (`-1`).  You use the same node order `(collector, base,
emitter)` — just connect with appropriate supply polarity.

## Typical Part Values

| Part | Type | $\beta_F$ | $I_S$ | $V_{AF}$ | Application |
|---|---|---|---|---|---|
| 2N2222 | NPN | 256 | `14.34e-15` | 74 V | General purpose |
| 2N3904 | NPN | 416 | `6.73e-15` | 74 V | General purpose |
| BC547 | NPN | 400 | `1.8e-14` | 80 V | Small signal |
| 2N3906 | PNP | 181 | `1.3e-14` | 18.7 V | General purpose |
| TIP31C | NPN | 50 | `1e-12` | 100 V | Medium power |
| TIP120 | NPN | 1000 | `6.8e-10` | 100 V | Darlington |

## Example — Common-Emitter Amplifier

```python
n_vcc = nm.AddNode("Vcc")
n_b   = nm.AddNode("base")
n_c   = nm.AddNode("collector")

ckt.AddComponent(DCVoltageSource("Vcc", (n_vcc, gnd), voltage=12))
ckt.AddComponent(Resistor("Rb", (n_vcc, n_b), resistance=100e3))
ckt.AddComponent(Resistor("Rc", (n_vcc, n_c), resistance=1e3))
ckt.AddComponent(NPN("Q1", (n_c, n_b, gnd), BF=200, Is=14.34e-15, Vaf=74))
```
