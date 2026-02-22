# Simulation Configuration

`SimulationConfig` is a Python dataclass that holds **every tuneable knob**
of the simulator.  Pass it to `Circuit()` at construction time; sensible
defaults are provided for all fields.

```python
from PyEEL import SimulationConfig, IntegrationMethod

config = SimulationConfig(
    dc_operating_point=True,
    integration_method=IntegrationMethod.BACKWARD_EULER,
)
ckt = Circuit(solver=NumpySolver(), config=config)
```

## Enums

### `SimulationMode`

| Value | Int | Meaning |
|---|---|---|
| `DC` | 1 | DC operating-point analysis |
| `AC` | 2 | Small-signal AC (future) |
| `TRANSIENT` | 3 | Time-domain transient analysis |

### `IntegrationMethod`

| Value | Int | Meaning |
|---|---|---|
| `BACKWARD_EULER` | 1 | First-order implicit — unconditionally stable, some damping |
| `TRAPEZOIDAL` | 2 | Second-order implicit — less damping, can ring on stiff systems |

## Configuration Parameters

### Integration

| Parameter | Default | Description |
|---|---|---|
| `integration_method` | `BACKWARD_EULER` | Numerical integration scheme for capacitors and inductors |
| `gmin` | `1e-12` | Minimum conductance added across every node pair to aid convergence |

### Time-Step Limits

| Parameter | Default | Description |
|---|---|---|
| `min_dt` | `1e-15` | Absolute floor on time step (seconds) |
| `max_dt` | `1.0` | Absolute ceiling on time step (seconds) |

### DC Operating Point

| Parameter | Default | Description |
|---|---|---|
| `dc_operating_point` | `True` | Solve the DC bias point before transient simulation begins |
| `dc_inductor_resistance` | `1e-9` | Small resistance placed in series with inductors during DC analysis (prevents singular matrix) |

### Adaptive Time-Step

By default the time step is fixed.  Enable adaptive stepping for circuits
with fast edges or widely varying dynamics.

| Parameter | Default | Description |
|---|---|---|
| `adaptive_timestep` | `False` | Enable adaptive time-step control |
| `adaptive_threshold` | `0.5` | Normalised change threshold to trigger step shrinking |
| `adaptive_shrink` | `0.5` | Multiply `dt` by this factor when step is rejected |
| `adaptive_grow` | `1.05` | Multiply `dt` by this factor when step is accepted |
| `max_grow_factor` | `2.0` | Maximum single-step growth ratio |

### Diagnostics

| Parameter | Default | Description |
|---|---|---|
| `condition_number_warning` | `1e15` | Log a warning when the MNA matrix condition number exceeds this |
| `energy_check` | `True` | Enable stored-energy sanity check each step |
| `max_energy` | `1e12` | Warn if total stored energy (capacitors + inductors) exceeds this |

### Newton–Raphson Iteration

These control the non-linear solver used for diodes, BJTs, MOSFETs.

| Parameter | Default | Description |
|---|---|---|
| `nr_max_iterations` | `50` | Maximum NR iterations per time step |
| `nr_abs_tolerance` | `1e-9` | Absolute convergence threshold on Δx |
| `nr_rel_tolerance` | `1e-6` | Relative convergence threshold |
| `nr_damping_enabled` | `True` | Use damped Newton steps |
| `nr_initial_damping` | `1.0` | Starting damping factor (1.0 = full step) |
| `nr_min_damping` | `0.01` | Minimum damping factor |
| `nr_vt_limit` | `0.25` | Maximum voltage change per NR step (thermal-voltage units) |

### Gmin Stepping

A fallback convergence technique: start with a large `gmin` (leakage
conductance) and gradually reduce it to the target value.

| Parameter | Default | Description |
|---|---|---|
| `gmin_stepping_enabled` | `True` | Enable gmin stepping as a convergence aid |
| `gmin_stepping_start` | `1e-3` | Starting gmin value |
| `gmin_stepping_factor` | `10.0` | Divide gmin by this each step |
| `gmin_stepping_min` | `1e-12` | Final (target) gmin value |

### Source Stepping

Another convergence aid: ramp source amplitudes from 0 to full value over
several steps.

| Parameter | Default | Description |
|---|---|---|
| `source_stepping_enabled` | `True` | Enable source stepping for DC OP |
| `source_stepping_steps` | `10` | Number of ramp steps |

## `SimulationContext`

`SimulationContext` is an internal dataclass that carries the **current state**
of the simulator to every `Stamp()` call.  You rarely interact with it
directly, but it's useful to understand:

| Field | Type | Description |
|---|---|---|
| `Mode` | `SimulationMode` | Current analysis type |
| `Time` | `float` | Current simulation time (seconds) |
| `dt` | `float` | Current time-step size |
| `x_prev` | `np.ndarray` | Solution vector from previous step |
| `x_current` | `np.ndarray` | Current iterate (during NR) |
| `Frequency` | `float` | For AC analysis |
| `Iteration` | `int` | Overall step counter |
| `is_nonlinear_iteration` | `bool` | True during NR inner loop |
| `source_factor` | `float` | 0 → 1 ramp during source stepping |
| `integration_method` | `IntegrationMethod` | Active integration scheme |
| `gmin` | `float` | Active gmin value |
