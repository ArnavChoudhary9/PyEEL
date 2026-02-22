# Newton–Raphson Solver

The Newton–Raphson (NR) solver handles circuits containing **non-linear**
components (diodes, BJTs, MOSFETs).  It iteratively linearises the
non-linear device equations until the solution converges.

## Algorithm

```
x = x_initial (previous time-step solution)
for iteration = 1, 2, …, max_iterations:
    1. Build A, b with components stamped at current x
    2. Solve:  Δx = A⁻¹ b − x
    3. Apply damping:  x_new = x + α · Δx
    4. Check convergence:
       - |Δx| < abs_tolerance  AND
       - |Δx| / |x_new| < rel_tolerance
    5. If converged → return x_new
       If not     → x = x_new, repeat
```

## Configuration Parameters

These are set via `SimulationConfig`:

| Parameter | Default | Description |
|---|---|---|
| `nr_max_iterations` | `50` | Maximum iterations before giving up |
| `nr_abs_tolerance` | `1e-9` | Absolute convergence: max ΔV or ΔI |
| `nr_rel_tolerance` | `1e-6` | Relative convergence: max ΔV/V or ΔI/I |
| `nr_damping_enabled` | `True` | Use damped steps to prevent oscillation |
| `nr_initial_damping` | `1.0` | Starting damping factor (1.0 = full Newton step) |
| `nr_min_damping` | `0.01` | Minimum damping factor |
| `nr_vt_limit` | `0.25` | Max voltage change per step in $V_T$ units |

## Damping

Full Newton steps can overshoot, especially near exponential I–V curves
(diode knee).  **Damped Newton** limits the step size:

$$
x_{k+1} = x_k + \alpha \cdot \Delta x
$$

where $\alpha \in [0.01, 1.0]$.  The damping factor is automatically
adjusted based on convergence progress.

## Voltage Limiting

For devices with exponential characteristics (diodes, BJT junctions), the
junction voltage change per NR iteration is limited to `nr_vt_limit × Vt`
to prevent numerical overflow in $e^{V/V_T}$.

## Dual Convergence Check

Convergence requires **both**:

1. **Absolute:** $\|\Delta x\|_\infty < $ `nr_abs_tolerance`
2. **Relative:** $\|\Delta x\|_\infty / \|x_{new}\|_\infty < $ `nr_rel_tolerance`

This ensures convergence on both small signals (mV) and large voltages (kV).

## Fallback: Gmin Stepping

If NR fails to converge, PyEEL can fall back to **gmin stepping**:

1. Start with a large gmin (e.g. `1e-3` S) — this linearises the circuit.
2. Solve with this artificially large leakage.
3. Gradually reduce gmin by a factor of 10 until reaching the target.
4. Each step uses the previous solution as the initial guess.

See [Convergence Helpers](convergence.md) for more details.
