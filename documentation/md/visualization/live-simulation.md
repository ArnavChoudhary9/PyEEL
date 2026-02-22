# Live Simulation

`LiveSimulation` ties together a `Circuit` and a `LivePlotter` into a
blocking simulation loop with interactive controls.

```python
from PyEEL import LiveSimulation

sim = LiveSimulation(ckt, plotter, dt=1e-4, speed=100)
sim.Run()
```

## Constructor

```python
LiveSimulation(circuit: Circuit, plotter: LivePlotter, *,
               dt: float = 0.0005, speed: int = 60,
               use_adaptive_dt: bool = False)
```

| Parameter | Default | Description |
|---|---|---|
| `circuit` | — | A finalised `Circuit` instance |
| `plotter` | — | A `LivePlotter` instance |
| `dt` | `0.0005` | Time step in seconds |
| `speed` | `60` | Simulation steps per frame |
| `use_adaptive_dt` | `False` | Use adaptive time-step control |

### `speed` Parameter

`speed` controls how many `Simulate(dt)` calls are made between each plot
update.  Higher values = faster simulation time progression, but less
responsive UI.

| speed | Effect |
|---|---|
| `20` | Slow, smooth — good for observing start-up |
| `60` | Balanced |
| `200` | Fast — good for reaching steady state quickly |

## Methods

| Method | Description |
|---|---|
| `Run()` | Start the simulation loop (blocking) |
| `Pause()` | Pause the simulation |
| `Resume()` | Resume from pause |
| `TogglePause()` | Toggle pause state |

## Properties

| Property | Type | Description |
|---|---|---|
| `IsPaused` | `bool` | Current pause state |
| `dt` | `float` | Time step (settable at runtime) |
| `Speed` | `int` | Steps per frame (settable at runtime) |

## Keyboard Controls

| Key | Action |
|---|---|
| **Space** | Toggle pause/resume |

## Lifecycle

```
sim.Run()
  ├── If dc_operating_point: SolveDCOperatingPoint()
  └── Loop:
       ├── for i in range(speed): circuit.Simulate(dt)
       ├── plotter.Update()
       └── Check if window closed → exit
```

The loop runs until the user closes the matplotlib window.

## Example

```python
config  = SimulationConfig(dc_operating_point=True)
ckt     = Circuit(solver=NumpySolver(), config=config)
# … add components and probes …
ckt.Finalize()

plotter = LivePlotter(
    [v_in, v_out],    # subplot 1
    [i_diode],         # subplot 2
    window=0.05,
)
sim = LiveSimulation(ckt, plotter, dt=1e-4, speed=100)
sim.Run()
```
