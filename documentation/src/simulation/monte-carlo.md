# Monte Carlo Analysis

Monte Carlo analysis performs statistical analysis of circuit behaviour under random component parameter variations. It runs the DC operating point many times, each time randomly perturbing component values according to specified tolerances, and collects the distribution of a measured output.

## How It Works

1. **Define tolerances** — specify which components vary and by how much.
2. **Random sampling** — for each run, component parameters are sampled from their tolerance distributions.
3. **DC solve** — the DC operating point is solved with the perturbed parameters.
4. **Measurement** — a user-defined function extracts the metric of interest from each solution.
5. **Statistics** — mean, standard deviation, min, max, and percentiles are computed across all runs.
6. **Restore** — original component values are restored after the analysis completes.

## The `Tolerance` Class

The `Tolerance` dataclass describes how a parameter varies. Use the factory methods:

| Factory Method | Distribution | Description |
|---|---|---|
| `Tolerance.percentage(pct)` | Uniform ±pct% | Resistor/capacitor manufacturing tolerance |
| `Tolerance.gaussian(mean, std)` | Gaussian | Device parameter with known mean and σ |
| `Tolerance.uniform(low, high)` | Uniform [low, high] | Parameter bounded between two absolute values |
| `Tolerance.gaussian_percent(pct)` | Gaussian, 3σ = pct% | Manufacturing spread as Gaussian |

## API

```python
mc_result = ckt.RunMonteCarlo(
    tolerances=[
        (component, "ParameterName", Tolerance.percentage(5)),
        # ... more tolerances
    ],
    num_runs=500,
    measure=lambda ckt, x_dc: x_dc[node.Index],
    seed=42,        # optional, for reproducibility
)
```

| Parameter | Type | Description |
|---|---|---|
| `tolerances` | `list[tuple]` | List of `(component, param_name, Tolerance)` tuples |
| `num_runs` | `int` | Number of random trials (default 100) |
| `measure` | `callable` | `measure(circuit, x_dc) → float` — extracts the metric from each run |
| `seed` | `int \| None` | Random seed for reproducibility |

## Return Value — `MonteCarloResult`

```python
@dataclass
class MonteCarloResult:
    num_runs: int
    values: np.ndarray       # shape (num_runs,)
    mean: float
    std: float
    min: float
    max: float
    percentile_5: float
    percentile_95: float
    parameter_samples: dict[str, np.ndarray]  # sampled values per parameter
```

| Field | Description |
|---|---|
| `num_runs` | Total number of completed runs |
| `values` | Array of measured outputs, one per run |
| `mean` | Mean of the measured values |
| `std` | Standard deviation |
| `min` / `max` | Extreme values |
| `percentile_5` / `percentile_95` | 5th and 95th percentile bounds |
| `parameter_samples` | Dictionary of sampled parameter arrays for correlation analysis |

## Example — Voltage Divider Tolerance

```python
from PyEEL import *

ckt = Circuit(solver=NumpySolver())

nm    = ckt.NodeManager
gnd   = nm.GroundNode
n_in  = nm.AddNode("n_in")
n_out = nm.AddNode("n_out")

ckt.AddComponent(DCVoltageSource("V1", (n_in, gnd), voltage=10.0))
r1 = Resistor("R1", (n_in, n_out), resistance=10e3)
r2 = Resistor("R2", (n_out, gnd), resistance=10e3)
ckt.AddComponent(r1)
ckt.AddComponent(r2)

ckt.Finalize()

def measure_vout(circuit, x_dc):
    return x_dc[n_out.Index]

mc_result = ckt.RunMonteCarlo(
    tolerances=[
        (r1, "Resistance", Tolerance.percentage(5)),
        (r2, "Resistance", Tolerance.percentage(5)),
    ],
    num_runs=500,
    measure=measure_vout,
    seed=42,
)

print(f"Mean: {mc_result.mean:.4f} V")
print(f"Std:  {mc_result.std:.4f} V")
print(f"Range: {mc_result.min:.4f} – {mc_result.max:.4f} V")

plot_monte_carlo(mc_result)
```

## Visualization

Use `plot_monte_carlo(result)` to display a histogram with statistical annotations:

```python
fig, ax = plot_monte_carlo(mc_result, bins=30, xlabel="V_out (V)")
```

The histogram shows the distribution of measured values with vertical lines for the mean, ±1σ, and 5th/95th percentiles.

See [Static Plotting](../visualization/plotting.md) for full details on plot customisation.
