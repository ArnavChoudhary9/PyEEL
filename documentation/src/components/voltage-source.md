# Voltage Source & Waveforms

An ideal independent voltage source that forces
$V(n_+) - V(n_-) = v(t)$.

```python
from PyEEL import DCVoltageSource, ACVoltageSource

ckt.AddComponent(DCVoltageSource("V1", (n1, gnd), voltage=5))
ckt.AddComponent(ACVoltageSource("Vac", (n1, gnd), amplitude=10, frequency=1e3))
```

## Factory Functions

### `DCVoltageSource`

```python
DCVoltageSource(name: str, nodes: tuple[Node, Node], voltage: float) -> VoltageSource
```

Creates a constant-voltage source.

| Parameter | Description |
|---|---|
| `voltage` | DC voltage in **Volts** |

### `ACVoltageSource`

```python
ACVoltageSource(name: str, nodes: tuple[Node, Node],
                amplitude: float, frequency: float) -> VoltageSource
```

Creates a sinusoidal voltage source: $v(t) = A \sin(2\pi f t)$.

| Parameter | Description |
|---|---|
| `amplitude` | Peak voltage in **Volts** (not RMS) |
| `frequency` | Frequency in **Hz** |

## Full Constructor (Custom Waveforms)

```python
VoltageSource(name: str, nodes: tuple[Node, Node], waveform: Waveform)
```

You can build any time-varying source by providing a `Waveform` object.

## Waveform Classes

### `ConstantWave`

```python
ConstantWave(value: float)
```

Returns the same value at all times. Used internally by `DCVoltageSource`.

### `SineWave`

```python
SineWave(frequency: float, amplitude: float = 1.0,
         phase: float = 0.0, dc_offset: float = 0.0)
```

$$
v(t) = A \sin(2\pi f t + \varphi) + V_{DC}
$$

| Parameter | Symbol | Default | Description |
|---|---|---|---|
| `frequency` | $f$ | — | Frequency in Hz |
| `amplitude` | $A$ | `1.0` | Peak amplitude in Volts |
| `phase` | $\varphi$ | `0.0` | Phase offset in **radians** |
| `dc_offset` | $V_{DC}$ | `0.0` | DC bias added to the sine |

### Creating Custom Waveforms

Subclass `Waveform` and implement `GetValue(context)`:

```python
from PyEEL.Components.Sources.Waveform import Waveform

class SquareWave(Waveform):
    def __init__(self, frequency, amplitude=1.0):
        self._f = frequency
        self._A = amplitude

    def GetValue(self, context):
        import math
        return self._A if math.sin(2 * math.pi * self._f * context.Time) >= 0 else -self._A

    @property
    def StaticValue(self):
        return 0.0
```

## MNA Stamp

A voltage source introduces one **auxiliary unknown** (the branch current
$I_{src}$) and stamps a KVL constraint row:

$$
V(n_+) - V(n_-) = v(t)
$$

The auxiliary unknown represents the current flowing **from $n_+$ to $n_-$
through the source** (conventional current direction).

## Source Stepping

During DC operating-point analysis, the source voltage is multiplied by a
`source_factor` that ramps from 0 to 1 over several steps.  This aids
convergence for circuits with strong non-linearities.

## Getting Source Current

```python
probe = CurrentProbe("I_V1", v1)
# or after solving:
i = v1.GetCurrent(solution_vector)
```
