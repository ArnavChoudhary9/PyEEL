# Common Building Blocks

The `common` module provides **circuit-topology factory functions** that
create groups of pre-wired components for standard sub-circuits.  Unlike
the [component library](overview.md) which provides individual parts,
`common` builds **complete sub-circuits**.

```python
from PyEEL.Components.common import voltage_divider, half_wave_rectifier, add_all
```

## Usage Pattern

Most functions return a `list[Component]` that you add to the circuit:

```python
components = voltage_divider("DIV", n_in, n_out, gnd, r_top=10e3, r_bottom=10e3)
add_all(ckt, components)
```

Some complex functions return a `(list[Component], dict)` tuple where the
dict contains internal nodes you may want to probe.

## Available Functions

### Passive Networks

#### `voltage_divider`

```python
voltage_divider(prefix, n_in, n_out, n_gnd, *, r_top, r_bottom) -> list[Component]
```

Two resistors forming a voltage divider: $V_{out} = V_{in} \cdot \dfrac{R_{bottom}}{R_{top} + R_{bottom}}$.

#### `rc_low_pass`

```python
rc_low_pass(prefix, n_in, n_out, n_gnd, *, resistance, capacitance) -> list[Component]
```

First-order low-pass filter.  Cutoff: $f_c = \dfrac{1}{2\pi RC}$.

#### `rc_high_pass`

```python
rc_high_pass(prefix, n_in, n_out, n_gnd, *, resistance, capacitance) -> list[Component]
```

First-order high-pass filter (coupling capacitor + resistor to ground).

#### `series_lcr`

```python
series_lcr(prefix, n_in, n_L_out, n_C_out, n_gnd, *,
           inductance, capacitance, resistance) -> list[Component]
```

Series L-C-R circuit.  Resonant frequency: $f_0 = \dfrac{1}{2\pi\sqrt{LC}}$.

#### `parallel_rc`

```python
parallel_rc(prefix, n_pos, n_neg, *, resistance, capacitance) -> list[Component]
```

Resistor and capacitor in parallel.

### Rectifiers

#### `half_wave_rectifier`

```python
half_wave_rectifier(prefix, n_ac, n_dc, n_gnd, *,
                    r_load, Is=1e-14, n_diode=1.0) -> list[Component]
```

Single diode + load resistor.

#### `full_bridge_rectifier`

```python
full_bridge_rectifier(prefix, n_ac_p, n_ac_n, n_dc_p, n_dc_n, *,
                      Is=1e-14, n_diode=1.0) -> list[Component]
```

Four diodes in a bridge configuration.

### Voltage Regulators

#### `zener_clamp`

```python
zener_clamp(prefix, n_in, n_out, n_gnd, *,
            r_series, Vz=5.1, Is=1e-14) -> list[Component]
```

Series resistor + Zener diode clipper.

#### `zener_regulator`

```python
zener_regulator(prefix, n_in, n_out, n_gnd, *,
                r_series, r_load, Vz=5.1, Is=1e-14) -> list[Component]
```

Shunt Zener regulator with load.

### Amplifiers

#### `ce_amplifier_with_nodes`

```python
ce_amplifier_with_nodes(prefix, node_manager, n_vcc, n_in, n_out, n_gnd, *,
                        r1, r2, rc, re, c_in, c_out,
                        BF=200, Is=1e-15, Vaf=None) -> (list, dict)
```

Complete voltage-divider-biased common-emitter NPN amplifier with coupling
capacitors.  Returns `(components, {'base': Node, 'collector': Node, 'emitter': Node})`.

#### `common_source_amplifier`

```python
common_source_amplifier(prefix, node_manager, n_vdd, n_in, n_out, n_gnd, *,
                        rd, rs, rg, c_in, c_out,
                        Kp=2e-5, Vth=1.0, lambda_=0.0,
                        mosfet_type=MOSFETType.NMOS) -> (list, dict)
```

MOSFET common-source amplifier.  Returns `(components, {'drain', 'gate', 'source'})`.

### Power Supplies

#### `dc_supply`

```python
dc_supply(prefix, n_vcc, n_gnd, *, voltage) -> list[Component]
```

Simple DC voltage source.

#### `ac_supply`

```python
ac_supply(prefix, n_out, n_gnd, *, amplitude, frequency) -> list[Component]
```

Simple AC voltage source.

#### `linear_power_supply`

```python
linear_power_supply(prefix, node_manager, n_ac_p, n_ac_n, n_dc_out, n_gnd, *,
                    r_load, c_filter=1000e-6, Is=1e-14) -> (list, dict)
```

Full-bridge rectifier + filter cap + load.

#### `transformer_supply`

```python
transformer_supply(prefix, node_manager, n_mains_p, n_mains_n,
                   n_dc_out, n_gnd, *, ...) -> (list, dict)
```

Complete linear power supply: transformer + bridge + filter + load.

### Utility

#### `add_all`

```python
add_all(circuit: Circuit, components: list[Component]) -> None
```

Convenience function to add a list of components to a circuit in one call.

### Op-Amp Circuits

#### `inverting_amplifier`

```python
inverting_amplifier(prefix, node_manager, n_in, n_out, n_gnd, *,
                    r_in=10e3, r_f=100e3,
                    A_OL=200_000, R_in_opamp=2e6, R_out_opamp=75.0
                    ) -> (list, {'inv_input'})
```

Inverting amplifier.  Gain ≈ $-R_f / R_{in}$.

#### `non_inverting_amplifier`

```python
non_inverting_amplifier(prefix, node_manager, n_in, n_out, n_gnd, *,
                        r1=10e3, r_f=90e3,
                        A_OL=200_000, R_in_opamp=2e6, R_out_opamp=75.0
                        ) -> (list, {'inv_input'})
```

Non-inverting amplifier.  Gain ≈ $1 + R_f / R_1$.

#### `voltage_follower`

```python
voltage_follower(prefix, node_manager, n_in, n_out, *,
                 A_OL=200_000, R_in_opamp=2e6, R_out_opamp=75.0
                 ) -> (list, {'feedback'})
```

Unity-gain buffer (gain = 1).  Uses a tiny wire resistor for the direct
output-to-inverting-input feedback connection.

#### `summing_amplifier`

```python
summing_amplifier(prefix, node_manager, input_nodes, n_out, n_gnd, *,
                  r_inputs=10e3, r_f=10e3,
                  A_OL=200_000, R_in_opamp=2e6, R_out_opamp=75.0
                  ) -> (list, {'summing_junction'})
```

Inverting summing amplifier with N inputs.  If all input resistors are
equal: $V_{out} = -(R_f / R_{in}) \cdot (V_1 + V_2 + \dots + V_N)$.

#### `difference_amplifier`

```python
difference_amplifier(prefix, node_manager, n_in_pos, n_in_neg, n_out, n_gnd, *,
                     r1=10e3, r2=10e3, r3=10e3, r_f=10e3,
                     A_OL=200_000, R_in_opamp=2e6, R_out_opamp=75.0
                     ) -> (list, {'inv_input', 'noninv_input'})
```

Difference (subtractor) amplifier.  When $R_1 = R_3$ and $R_2 = R_f$:
$V_{out} = (R_f / R_1) \cdot (V_{pos} - V_{neg})$.

#### `integrator`

```python
integrator(prefix, node_manager, n_in, n_out, n_gnd, *,
           r_in=10e3, c_f=100e-9,
           A_OL=200_000, R_in_opamp=2e6, R_out_opamp=75.0
           ) -> (list, {'inv_input'})
```

Inverting integrator.  $V_{out}(t) = -\dfrac{1}{RC} \int V_{in} \, dt$.

#### `differentiator`

```python
differentiator(prefix, node_manager, n_in, n_out, n_gnd, *,
               c_in=100e-9, r_f=10e3,
               A_OL=200_000, R_in_opamp=2e6, R_out_opamp=75.0
               ) -> (list, {'inv_input'})
```

Inverting differentiator.  $V_{out}(t) = -R_f C \dfrac{dV_{in}}{dt}$.
