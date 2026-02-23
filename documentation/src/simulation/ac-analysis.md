# AC Small-Signal Analysis

AC analysis linearises the circuit around its DC operating point, replaces reactive elements with their complex impedances, and sweeps frequency to produce Bode-plot data (magnitude and phase vs frequency).

## How It Works

1. **DC operating point** — the circuit is solved for its quiescent state. All nonlinear devices (diodes, BJTs, MOSFETs) are replaced by their small-signal conductances at the bias point.
2. **Linearised MNA matrix** — a conductance matrix **G** is built from the linearised models.
3. **Frequency sweep** — for each frequency *f* in the sweep range:
   - A susceptance matrix **C** is constructed (capacitors contribute *jωC*, inductors contribute *1/(jωL)*).
   - The complex system **(G + jωC) · x_ac = b_ac** is solved.
   - Magnitude and phase of the transfer function *H(jω) = V_out / V_in* are extracted.

## API

```python
ac_result = ckt.RunAC(
    f_start,                        # start frequency (Hz)
    f_stop,                         # stop frequency (Hz)
    num_points,                     # number of frequency points
    input_source_name=None,         # name of the AC excitation source
    output_node_index=None,         # node index for V_out
    log_scale=True,                 # logarithmic frequency spacing
)
```

| Parameter | Type | Description |
|---|---|---|
| `f_start` | `float` | Start frequency in Hz |
| `f_stop` | `float` | Stop frequency in Hz |
| `num_points` | `int` | Number of frequency points (default 100) |
| `input_source_name` | `str \| None` | Name of the AC voltage source (1 V excitation). If `None`, the first `ACVoltageSource` is used. |
| `output_node_index` | `int \| None` | Node index whose voltage defines the output |
| `log_scale` | `bool` | Use logarithmic spacing (default `True`) |

The circuit must be finalized before calling `RunAC`. If the DC operating point has not yet been solved, it is computed automatically.

## Return Value — `ACResult`

```python
@dataclass
class ACResult:
    frequencies: np.ndarray       # Hz — shape (num_points,)
    magnitude_dB: np.ndarray      # 20·log10(|H|)
    phase_deg: np.ndarray         # degrees
    complex_response: np.ndarray  # raw complex H(jω)
```

| Field | Description |
|---|---|
| `frequencies` | Array of frequency points in Hz |
| `magnitude_dB` | Transfer function magnitude in decibels |
| `phase_deg` | Transfer function phase in degrees |
| `complex_response` | Raw complex-valued transfer function for custom post-processing |

## Example — RC Low-Pass Filter

```python
from PyEEL import *
import numpy as np

ckt = Circuit(solver=NumpySolver())

nm    = ckt.NodeManager
gnd   = nm.GroundNode
n_in  = nm.AddNode("n_in")
n_out = nm.AddNode("n_out")

v1 = ACVoltageSource("V1", (n_in, gnd), amplitude=1.0, frequency=1000.0)
r1 = Resistor("R1", (n_in, n_out), resistance=1e3)
c1 = Capacitor("C1", (n_out, gnd), capacitance=100e-9)

ckt.AddComponent(v1)
ckt.AddComponent(r1)
ckt.AddComponent(c1)

ckt.Finalize()

# Sweep from 1 Hz to 1 MHz with 200 points
ac_result = ckt.RunAC(
    1.0, 1e6, 200,
    input_source_name="V1",
    output_node_index=n_out.Index,
)

# Find the -3 dB frequency
idx_3dB = np.argmin(np.abs(ac_result.magnitude_dB - (-3.0)))
f_3dB = ac_result.frequencies[idx_3dB]
print(f"-3 dB frequency: {f_3dB:.1f} Hz")

# Plot the Bode diagram
plot_bode(ac_result)
```

The theoretical cutoff frequency for this RC filter is:

$$f_c = \frac{1}{2\pi R C} = \frac{1}{2\pi \cdot 1\,\text{k}\Omega \cdot 100\,\text{nF}} \approx 1592\,\text{Hz}$$

## Visualization

Use `plot_bode(result)` to generate a Bode plot with magnitude and phase subplots:

```python
fig, (ax_mag, ax_phase) = plot_bode(ac_result, title="RC Filter Response")
```

See [Static Plotting](../visualization/plotting.md) for full details on plot customisation.
