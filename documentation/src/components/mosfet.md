# MOSFET

Models N-channel and P-channel MOSFETs using the **Level-1 Shichman–Hodges**
model with three operating regions: cutoff, linear (triode), and saturation.

```python
from PyEEL import MOSFET, MOSFETType, NMOS, PMOS

# Full constructor
ckt.AddComponent(MOSFET("M1", (n_d, n_g, n_s), MOSFETType.NMOS, Kp=2e-3, Vth=1.5))

# Convenience factories
ckt.AddComponent(NMOS("M1", (n_d, n_g, n_s), Kp=2e-3, Vth=1.5))
ckt.AddComponent(PMOS("M2", (n_d, n_g, n_s), Kp=1e-3, Vth=-1.5))
```

## Constructor

```python
MOSFET(name: str, nodes: tuple[Node, Node, Node],
       mosfet_type=MOSFETType.NMOS, *,
       Kp=2e-5, Vth=1.0, lambda_=0.0)
```

| Parameter | Symbol | Default | Description |
|---|---|---|---|
| `name` | — | — | Unique component name |
| `nodes` | — | — | `(drain, gate, source)` |
| `mosfet_type` | — | `NMOS` | `MOSFETType.NMOS` or `MOSFETType.PMOS` |
| `Kp` | $K_p$ | `2e-5` | **Transconductance parameter** (A/V²). $K_p = \mu_n C_{ox} (W/L)$. |
| `Vth` | $V_{th}$ | `1.0` | **Threshold voltage** (V). Gate voltage above which the channel forms. |
| `lambda_` | $\lambda$ | `0.0` | **Channel-length modulation** (1/V). Models finite output resistance. |

## `MOSFETType` Enum

| Value | Int | Description |
|---|---|---|
| `NMOS` | `1` | N-channel enhancement MOSFET |
| `PMOS` | `-1` | P-channel enhancement MOSFET |

## Properties

| Property | Type | Description |
|---|---|---|
| `Type` | `MOSFETType` | NMOS or PMOS |
| `Kp` | `float` | Transconductance parameter |
| `Vth` | `float` | Threshold voltage |

## Operating Regions

For NMOS ($V_{GS}$, $V_{DS}$ measured relative to source):

### Cutoff ($V_{GS} < V_{th}$)

$$
I_D = 0
$$

The MOSFET is off.

### Linear / Triode ($V_{GS} \geq V_{th}$ and $V_{DS} < V_{GS} - V_{th}$)

$$
I_D = K_p \left[ (V_{GS} - V_{th}) \cdot V_{DS} - \frac{V_{DS}^2}{2} \right] (1 + \lambda V_{DS})
$$

The MOSFET acts like a voltage-controlled resistor.

### Saturation ($V_{GS} \geq V_{th}$ and $V_{DS} \geq V_{GS} - V_{th}$)

$$
I_D = \frac{K_p}{2} (V_{GS} - V_{th})^2 (1 + \lambda V_{DS})
$$

The MOSFET acts like a voltage-controlled current source — the amplifying
region.

### Physical Meaning of Parameters

- **$K_p$ (Transconductance Parameter):** Combines the intrinsic mobility,
  oxide capacitance, and device geometry: $K_p = \mu C_{ox} \frac{W}{L}$.
  Larger $K_p$ → more current for the same $V_{GS}$.

- **$V_{th}$ (Threshold Voltage):** The gate-source voltage at which the
  channel begins to conduct.  Typical: 0.5–3 V for enhancement-mode devices.

- **$\lambda$ (Channel-Length Modulation):** Models the slope of $I_D$ vs
  $V_{DS}$ in saturation.  Output resistance: $r_o = 1/(\lambda I_D)$.
  Set to `0.0` for an ideal (infinite $r_o$) device.

## PMOS Transistors

For PMOS, all polarities are inverted internally.  Use the same node order
`(drain, gate, source)` — the PMOS conducts when $V_{SG} > |V_{th}|$.

## Example — Common-Source Amplifier

```python
n_vdd = nm.AddNode("Vdd")
n_g   = nm.AddNode("gate")
n_d   = nm.AddNode("drain")

ckt.AddComponent(DCVoltageSource("Vdd", (n_vdd, gnd), voltage=5))
ckt.AddComponent(Resistor("Rd", (n_vdd, n_d), resistance=1e3))
ckt.AddComponent(Resistor("Rg", (n_g, gnd), resistance=1e6))
ckt.AddComponent(NMOS("M1", (n_d, n_g, gnd), Kp=2e-3, Vth=1.0))
```
