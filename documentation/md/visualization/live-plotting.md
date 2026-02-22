# Live Plotting

`LivePlotter` provides real-time animated matplotlib plots that update
as the simulation runs.

```python
from PyEEL import LivePlotter
```

## Constructor

```python
LivePlotter(*groups: list[Probe], window: float | None = None,
            update_interval: float = 0.03)
```

| Parameter | Default | Description |
|---|---|---|
| `*groups` | — | Each positional argument is a `list[Probe]` that shares one subplot |
| `window` | `None` | Sliding time window in seconds. `None` shows the full history. |
| `update_interval` | `0.03` | Minimum seconds between plot refreshes (≈ 33 fps) |

## Subplot Groups

Each positional argument to `LivePlotter` creates a **separate subplot**:

```python
plotter = LivePlotter(
    [v_in_probe, v_out_probe],      # subplot 1: two voltage traces
    [i_probe],                       # subplot 2: one current trace
    window=0.05,                     # show last 50 ms
)
```

This creates a figure with 2 vertically stacked subplots.

## Properties

| Property | Type | Description |
|---|---|---|
| `IsOpen` | `bool` | Whether the plot window is still open |

## Methods

| Method | Description |
|---|---|
| `Update()` | Refresh the plot with latest probe data. Called automatically by `LiveSimulation`. |
| `Close()` | Close the matplotlib window |
| `KeepOpen()` | Block until the user closes the window (useful at script end) |

## Standalone Usage

You can use `LivePlotter` without `LiveSimulation` by calling `Update()`
manually:

```python
plotter = LivePlotter([v_probe], window=0.1)

for _ in range(50_000):
    ckt.Simulate(dt=1e-4)
    plotter.Update()

plotter.KeepOpen()
```

## Tips

- **Window size:** Set `window` to 2–3 periods of your signal for a clean
  display.  For 50 Hz → `window=0.06`.
- **Performance:** The `update_interval` throttles redraws.  Increase it
  if the simulation is slow.
- **Multiple windows:** Create multiple `LivePlotter` instances for
  separate windows.
