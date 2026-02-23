# Parameter Sweep

Parameter sweep analysis varies one or two component parameters across a specified range, running the DC operating point at each point and collecting a measured output.

## How It Works

1. **Register parameters** — specify which component parameters to sweep and over what range.
2. **Iterate** — for each combination of parameter values:
   - Set the component parameter.
   - Solve the DC operating point.
   - Call the measurement function.
3. **Collect** — results are gathered into an array (1-D for single-parameter sweeps, 2-D for dual-parameter sweeps).
4. **Restore** — original parameter values are restored after the sweep completes.

## API

```python
sweep_result = ckt.RunSweep(
    parameters=[
        (component, "ParameterName", start, stop, num_points),
        # ... optionally a second parameter for 2-D sweep
    ],
    measure=lambda ckt, x_dc: x_dc[node.Index],
)
```

| Parameter | Type | Description |
|---|---|---|
| `parameters` | `list[tuple]` | Each entry: `(component, param_name, start, stop, num)` |
| `measure` | `callable` | `measure(circuit, x_dc) → float` — extracts the metric at each sweep point |

Each parameter tuple can take these forms:

| Format | Description |
|---|---|
| `(comp, "Resistance", 1e3, 100e3, 20)` | Linear sweep from 1 kΩ to 100 kΩ in 20 steps |
| `(comp, "Resistance", [1e3, 2.2e3, 4.7e3, 10e3])` | Explicit list of values |

## Return Value — `SweepResult`

```python
@dataclass
class SweepResult:
    sweep_values: dict[str, np.ndarray]  # parameter name → array of values
    measured: np.ndarray                  # shape depends on sweep dimensions
```

| Field | Description |
|---|---|
| `sweep_values` | Dictionary mapping parameter labels to their swept value arrays |
| `measured` | 1-D array for single sweeps; 2-D array `(num_A, num_B)` for dual sweeps |

## Example — Voltage Divider Sweep

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

sweep_result = ckt.RunSweep(
    parameters=[
        (r1, "Resistance", 1e3, 100e3, 20),
    ],
    measure=measure_vout,
)

# Print sample points
r_values = sweep_result.sweep_values["R1.Resistance"]
v_values = sweep_result.measured
for r, v in zip(r_values, v_values):
    print(f"  R1 = {r:>9.0f} Ω  →  V_out = {v:.4f} V")

plot_sweep(sweep_result)
```

### Dual-Parameter Sweep

For a 2-D sweep, add a second parameter tuple. The result is a 2-D array rendered as a heatmap:

```python
sweep_result = ckt.RunSweep(
    parameters=[
        (r1, "Resistance", 1e3, 100e3, 20),
        (r2, "Resistance", 1e3, 100e3, 20),
    ],
    measure=measure_vout,
)
# sweep_result.measured.shape == (20, 20)
plot_sweep(sweep_result)
```

## Visualization

Use `plot_sweep(result)` to automatically generate the appropriate plot:

- **Single-parameter sweep** → line plot (value vs parameter)
- **Dual-parameter sweep** → 2-D heatmap with colour bar

```python
fig, ax = plot_sweep(sweep_result, ylabel="V_out (V)", log_x=True)
```

See [Static Plotting](../visualization/plotting.md) for full details on plot customisation.
