# Harmonic Balance Analysis

Harmonic Balance (HB) finds the periodic steady state of a nonlinear circuit driven by a single-tone excitation **without** running a long transient simulation. It represents node voltages as truncated Fourier series and iteratively balances currents from the linear sub-network (in the frequency domain) with those from the nonlinear sub-network (in the time domain via DFT/IDFT).

## How It Works

1. **Fourier decomposition** — node voltages are expanded as a truncated series up to the *K*-th harmonic: DC, *f₀*, 2*f₀*, … , *Kf₀*.
2. **Linear sub-network** — resistors, capacitors, and inductors are evaluated in the frequency domain at each harmonic.
3. **Nonlinear sub-network** — diodes, BJTs, and MOSFETs are evaluated in the time domain by sampling one period with 2*K*+1 points and applying the DFT.
4. **Newton iteration** — the combined frequency-domain residual is driven to zero using Newton-Raphson until convergence.

This is especially useful for:

- **Mixers and oscillators** where the transient settling time is long.
- **Distortion analysis** — directly reveals harmonic content.
- **RF circuits** — periodic steady state at GHz frequencies without picosecond time steps.

## API

```python
hb_result = ckt.RunHarmonicBalance(
    fundamental,              # fundamental frequency (Hz)
    num_harmonics=7,          # number of harmonics K
    max_iter=200,             # maximum Newton iterations
    tol=1e-6,                 # convergence tolerance
)
```

| Parameter | Type | Description |
|---|---|---|
| `fundamental` | `float` | Fundamental frequency in Hz |
| `num_harmonics` | `int` | Number of harmonics *K* (default 7). Total tones = *K*+1 including DC. |
| `max_iter` | `int` | Maximum Newton iterations (default 200) |
| `tol` | `float` | Convergence tolerance on norm of residual (default 1e-6) |

The circuit must be finalized. The DC operating point is solved automatically if not already computed.

## Return Value — `HBResult`

```python
@dataclass
class HBResult:
    fundamental: float          # Hz
    num_harmonics: int          # K
    frequencies: np.ndarray     # shape (K+1,) — [0, f, 2f, ..., Kf]
    spectrum: np.ndarray        # complex, shape (N_nodes, K+1)
    converged: bool
    iterations: int
    residual: float
```

| Field | Description |
|---|---|
| `fundamental` | The fundamental frequency used |
| `num_harmonics` | Number of harmonics *K* |
| `frequencies` | Array of harmonic frequencies: 0, *f₀*, 2*f₀*, … |
| `spectrum` | Complex Fourier coefficients per node. `spectrum[node_idx, k]` gives the *k*-th harmonic phasor at node `node_idx`. |
| `converged` | `True` if Newton iteration converged within `max_iter` |
| `iterations` | Number of Newton iterations performed |
| `residual` | Final residual norm |

## Example — Diode Clipper

```python
from PyEEL import *

config = SimulationConfig(dc_operating_point=True, gmin=1e-12)
ckt = Circuit(solver=NumpySolver(), config=config)

nm    = ckt.NodeManager
gnd   = nm.GroundNode
n_in  = nm.AddNode("n_in")
n_out = nm.AddNode("n_out")

ckt.AddComponent(ACVoltageSource("V1", (n_in, gnd),
                                 amplitude=2.0, frequency=1000.0))
ckt.AddComponent(Resistor("R1", (n_in, n_out), resistance=1e3))
ckt.AddComponent(Diode("D1", (n_out, gnd)))
ckt.AddComponent(Resistor("R_load", (n_out, gnd), resistance=10e3))

ckt.Finalize()

hb_result = ckt.RunHarmonicBalance(
    fundamental=1000.0,
    num_harmonics=7,
)

print(f"Converged: {hb_result.converged}")
print(f"Iterations: {hb_result.iterations}")
print(f"Residual: {hb_result.residual:.2e}")

# Print the harmonic magnitudes at the output node
node_spectrum = abs(hb_result.spectrum[:, n_out.Index])
for i, (freq, mag) in enumerate(zip(hb_result.frequencies,
                                    node_spectrum)):
    label = "DC" if i == 0 else f"H{i}"
    print(f"  {label:>3s}  {freq:>10.0f} Hz   {mag:.4f} V")

plot_harmonic_spectrum(hb_result)
```

The diode clips the positive half-cycle, producing significant harmonic distortion visible in the bar chart.

## Visualization

Use `plot_harmonic_spectrum(result)` to display harmonic magnitudes as a bar chart:

```python
fig, ax = plot_harmonic_spectrum(hb_result, node_index=0, title="Clipper Spectrum")
```

The `node_index` parameter selects which node's spectrum to plot (default 0 = first node).

See [Static Plotting](../visualization/plotting.md) for full details on plot customisation.
