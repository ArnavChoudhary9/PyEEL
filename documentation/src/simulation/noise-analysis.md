# Noise Analysis

Noise analysis computes the output-referred noise spectral density at a specified node by propagating individual component noise contributions through the linearised small-signal transfer function.

## How It Works

1. **DC operating point** — solved to determine bias currents and voltages for all devices.
2. **Linearised MNA** — small-signal conductance matrix **G** is built at the operating point.
3. **Per-frequency sweep** — for each frequency *f*:
   - Build the complex admittance matrix **Y(jω) = G + jωC**.
   - For each noisy component, inject a unit noise current and compute the transfer impedance to the output node.
   - Weight by the component's spectral density and sum in RSS (root sum of squares).
4. **Integration** — the total noise spectral density is integrated over the bandwidth to yield the RMS noise voltage.

### Noise Sources

| Source Type | Spectral Density | Applies To |
|---|---|---|
| Thermal (Johnson–Nyquist) | $S_v = 4 k T R$ | Resistors |
| Shot noise | $S_i = 2 q I_d$ | Diodes, BJT junctions |

where $k$ is Boltzmann's constant and $q$ is the electron charge.

## API

```python
noise_result = ckt.RunNoise(
    f_start,                       # start frequency (Hz)
    f_stop,                        # stop frequency (Hz)
    num_points,                    # number of frequency points
    output_node_index=idx,         # node index for output-referred noise
)
```

| Parameter | Type | Description |
|---|---|---|
| `f_start` | `float` | Start frequency in Hz |
| `f_stop` | `float` | Stop frequency in Hz |
| `num_points` | `int` | Number of frequency points (default 100) |
| `output_node_index` | `int` | Node index where noise is measured (required) |
| `log_scale` | `bool` | Use logarithmic spacing (default `True`) |

## Return Value — `NoiseResult`

```python
@dataclass
class NoiseResult:
    frequencies: np.ndarray                        # Hz
    output_noise_density: np.ndarray               # V²/Hz
    integrated_noise_vrms: float                   # total RMS noise (V)
    component_contributions: dict[str, np.ndarray] # per-component breakdown
```

| Field | Description |
|---|---|
| `frequencies` | Array of frequency points in Hz |
| `output_noise_density` | Output-referred noise spectral density (V²/Hz) at each frequency |
| `integrated_noise_vrms` | Integrated RMS noise voltage over the full bandwidth |
| `component_contributions` | Dictionary mapping component name → spectral density array. Useful for identifying dominant noise sources. |

## Example — Resistive Voltage Divider

```python
from PyEEL import *

ckt = Circuit(solver=NumpySolver())

nm    = ckt.NodeManager
gnd   = nm.GroundNode
n_in  = nm.AddNode("n_in")
n_out = nm.AddNode("n_out")

ckt.AddComponent(DCVoltageSource("V1", (n_in, gnd), voltage=5.0))
ckt.AddComponent(Resistor("R1", (n_in, n_out), resistance=10e3))
ckt.AddComponent(Resistor("R2", (n_out, gnd), resistance=10e3))

ckt.Finalize()

noise_result = ckt.RunNoise(
    10.0, 100e3, 200,
    output_node_index=n_out.Index,
)

print(f"Integrated RMS noise: {noise_result.integrated_noise_vrms * 1e6:.2f} µV")

# Per-component contributions
if noise_result.component_contributions:
    mid = len(noise_result.frequencies) // 2
    for name, contrib in noise_result.component_contributions.items():
        print(f"  {name}: {contrib[mid]:.4e} V²/Hz (at {noise_result.frequencies[mid]:.0f} Hz)")

# Visualise
plot_noise_spectrum(noise_result)
```

## Visualization

Use `plot_noise_spectrum(result)` to display the spectral density on a log-log plot:

```python
fig, ax = plot_noise_spectrum(noise_result, show_components=True)
```

When `show_components=True` (the default), individual component noise traces are overlaid so you can identify the dominant noise contributor.

See [Static Plotting](../visualization/plotting.md) for full details on plot customisation.
