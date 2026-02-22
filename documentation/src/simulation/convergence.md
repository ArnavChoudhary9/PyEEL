# Convergence Helpers

Non-linear circuits can be difficult to solve.  PyEEL provides several
convergence aids that activate automatically when Newton–Raphson struggles.

## Gmin Stepping

**Problem:** With very small `gmin`, some circuits have nearly singular
matrices and NR cannot find a starting point.

**Solution:** Start with a large gmin (e.g. `1e-3` S — significant leakage)
and solve.  Then gradually reduce gmin by a factor of 10 toward the target
value, using each solution as the starting point for the next.

```python
config = SimulationConfig(
    gmin_stepping_enabled=True,      # default: True
    gmin_stepping_start=1e-3,        # initial gmin
    gmin_stepping_factor=10.0,       # divide by this each step
    gmin_stepping_min=1e-12,         # final target gmin
)
```

### How It Works

```
gmin = 1e-3   → solve → converges ✓
gmin = 1e-4   → solve → converges ✓
gmin = 1e-5   → solve → converges ✓
   …
gmin = 1e-12  → solve → converges ✓  (final answer)
```

## Source Stepping

**Problem:** Large source voltages applied to non-linear circuits can
cause NR to diverge from a zero initial guess.

**Solution:** Ramp all source amplitudes from 0 to their full value over
several steps.

```python
config = SimulationConfig(
    source_stepping_enabled=True,    # default: True
    source_stepping_steps=10,        # number of ramp steps
)
```

### How It Works

```
source_factor = 0.1  → all sources at 10%  → solve ✓
source_factor = 0.2  → all sources at 20%  → solve ✓
   …
source_factor = 1.0  → all sources at 100% → solve ✓  (final answer)
```

## Voltage Limiting

For exponential devices (diodes, BJT junctions), the voltage change per NR
iteration is clamped:

$$
\Delta V_{junction} \leq n_{vt\_limit} \cdot V_T
$$

Default: `nr_vt_limit = 0.25` (about 6.5 mV change per iteration). This
prevents $e^{V/V_T}$ from overflowing.

## Damped Newton

The Newton step is scaled by a factor $\alpha$:

$$
x_{k+1} = x_k + \alpha \cdot \Delta x
$$

$\alpha$ starts at `nr_initial_damping` (default 1.0 = full step) and is
reduced if the residual increases.

## Topology Validation

`Finalize()` runs a topology check that catches common wiring mistakes:

| Check | What It Catches |
|---|---|
| Isolated nodes | Nodes connected to only one component terminal |
| Capacitor-only nodes | Nodes connected only to capacitors (infinite impedance at DC) |
| Voltage source loops | Two voltage sources in parallel (contradictory constraints) |
| Extreme values | Very large or very small component values that may cause numerical issues |

## Energy Check

Each transient step, the total stored energy in capacitors and inductors is
computed:

$$
E_{total} = \sum \frac{1}{2} C V^2 + \sum \frac{1}{2} L I^2
$$

If `E_total > max_energy` (default `1e12`), a warning is logged.  This
catches runaway simulations early.

## Troubleshooting Guide

| Symptom | Likely Cause | Fix |
|---|---|---|
| "NR failed to converge" | Stiff circuit, bad initial guess | Increase `nr_max_iterations`; enable source stepping |
| Oscillating NR | Large voltage swings | Reduce `nr_vt_limit`; enable damping |
| Singular matrix | Floating node, VS loop | Check wiring; add bias resistors |
| Energy warning | Unstable simulation | Reduce `dt`; check component values |
| Slow convergence | Tight tolerances | Relax `nr_abs_tolerance` slightly |
