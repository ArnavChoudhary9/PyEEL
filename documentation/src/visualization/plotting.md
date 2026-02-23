# Static Plotting

PyEEL includes six plotting functions that generate publication-quality figures from analysis result objects. All functions live in `PyEEL.Visualization.Plotting` and are available via `from PyEEL import *`.

## Requirements

- **matplotlib** must be installed (`pip install matplotlib`).
- matplotlib is imported lazily — the rest of PyEEL works without it. If missing and you call a plot function, a helpful `ImportError` is raised.

## Common Conventions

All plotting functions share these patterns:

| Convention | Detail |
|---|---|
| **Return value** | `(fig, ax)` or `(fig, (ax1, ax2))` for multi-axis plots |
| **`show` parameter** | `True` by default — calls `plt.show()`. Set `show=False` for batch processing or further customisation. |
| **`title` parameter** | Custom figure title |
| **`figsize` parameter** | Matplotlib figure size tuple, e.g. `(10, 5)` |

Because every function returns the matplotlib figure and axes objects, you can always customise the plot further before displaying or saving:

```python
fig, ax = plot_noise_spectrum(result, show=False)
ax.set_xlim(100, 50e3)
fig.savefig("noise.png", dpi=150)
```

---

## `plot_bode`

Generates a Bode diagram (magnitude + phase) from an AC analysis result.

```python
fig, (ax_mag, ax_phase) = plot_bode(
    result,                   # ACResult
    title="Bode Plot",
    figsize=(10, 6),
    mag_label="Magnitude (dB)",
    phase_label="Phase (°)",
    show=True,
)
```

- **Input:** `ACResult` from `ckt.RunAC()`
- **Output:** Two vertically stacked subplots — semilog-x magnitude (dB) and phase (degrees).

---

## `plot_noise_spectrum`

Displays noise spectral density on a log-log plot.

```python
fig, ax = plot_noise_spectrum(
    result,                   # NoiseResult
    title="Noise Spectral Density",
    figsize=(10, 5),
    show_components=True,
    ylabel=r"Noise density (V²/Hz)",
    show=True,
)
```

- **Input:** `NoiseResult` from `ckt.RunNoise()`
- **Output:** Log-log plot of total output noise. When `show_components=True` and per-component data is available, individual traces are overlaid with a legend.
- The title automatically includes the integrated RMS noise value.

---

## `plot_monte_carlo`

Plots a histogram of Monte Carlo measured values with statistical annotations.

```python
fig, ax = plot_monte_carlo(
    result,                   # MonteCarloResult
    title="Monte Carlo Distribution",
    figsize=(10, 5),
    bins="auto",
    xlabel="Measured value",
    show_stats=True,
    show=True,
)
```

- **Input:** `MonteCarloResult` from `ckt.RunMonteCarlo()`
- **Output:** Histogram with vertical lines for mean, ±1σ, and 5th/95th percentiles (when `show_stats=True`).

---

## `plot_sweep`

Plots parameter sweep results — automatically selects the correct plot type.

```python
fig, ax = plot_sweep(
    result,                   # SweepResult
    title="Parameter Sweep",
    figsize=(10, 5),
    ylabel="Measured value",
    log_x=False,
    show=True,
)
```

- **Input:** `SweepResult` from `ckt.RunSweep()`
- **Output:**
  - **Single-parameter:** line plot with markers.
  - **Dual-parameter:** 2-D heatmap with colour bar.
- Set `log_x=True` for logarithmic x-axis on single-parameter sweeps.

---

## `plot_harmonic_spectrum`

Displays harmonic magnitudes from a Harmonic Balance result as a bar chart.

```python
fig, ax = plot_harmonic_spectrum(
    result,                   # HBResult
    node_index=0,
    title="Harmonic Spectrum",
    figsize=(10, 5),
    show=True,
)
```

- **Input:** `HBResult` from `ckt.RunHarmonicBalance()`
- **Output:** Bar chart of harmonic magnitudes. The title includes convergence status, iteration count, and residual.
- `node_index` selects which node's spectrum to display (default 0).

---

## `plot_transient`

Plots one or more time-domain waveforms.

```python
fig, ax = plot_transient(
    time,                     # np.ndarray — time axis (s)
    signals,                  # dict[str, np.ndarray] — label → data
    title="Transient Simulation",
    figsize=(10, 5),
    ylabel="Voltage / Current",
    show=True,
)
```

- **Input:** Time array and a dictionary of named signal arrays.
- **Output:** Line plot with one trace per signal and a legend.

```python
# Example: plot two signals
plot_transient(t, {
    "V(out)": v_out_array,
    "V(in)": v_in_array,
})
```

---

## Batch Processing Example

When generating multiple figures for a report, disable `show` and save each figure:

```python
fig1, _ = plot_bode(ac_result, show=False)
fig1.savefig("bode.png", dpi=150)

fig2, _ = plot_monte_carlo(mc_result, show=False)
fig2.savefig("monte_carlo.png", dpi=150)

fig3, _ = plot_sweep(sweep_result, show=False)
fig3.savefig("sweep.png", dpi=150)
```
