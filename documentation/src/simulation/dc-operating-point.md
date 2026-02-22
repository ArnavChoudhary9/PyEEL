# DC Operating Point

The DC operating-point solver finds the **steady-state bias** of the circuit
with all time-varying terms removed.  This is the starting point for
transient analysis.

## What Happens During DC OP

| Component | DC Behaviour |
|---|---|
| Resistor | Normal |
| Capacitor | **Open circuit** (removed from MNA) |
| Inductor | **Short circuit** (tiny resistance `dc_inductor_resistance`) |
| DC Source | Normal |
| AC Source | Evaluates to its DC offset (0 for pure sine) |
| Diode / BJT / MOSFET | Solved by Newton–Raphson |

## Solver Flow

```
1. Set SimulationMode = DC
2. If circuit is purely linear:
      → Single A·x = b solve
3. If circuit has non-linear components:
      a. Try Newton–Raphson from zero initial guess
      b. If NR fails → try source stepping:
         - Ramp source amplitudes from 0% → 100%
         - Solve at each step, using previous as initial guess
      c. If source stepping fails → try gmin stepping
4. Store solution as x_prev for transient analysis
```

## Configuration

| Parameter | Default | Effect |
|---|---|---|
| `dc_operating_point` | `True` | Set to `False` to skip DC OP and start transient from zero |
| `dc_inductor_resistance` | `1e-9` | Resistance for inductor DC model (prevents singular matrix) |
| `source_stepping_enabled` | `True` | Enable source ramping fallback |
| `source_stepping_steps` | `10` | Number of ramp steps (more = slower but more robust) |
| `gmin_stepping_enabled` | `True` | Enable gmin ramping fallback |

## When to Disable DC OP

Set `dc_operating_point=False` when:

- The circuit has **no DC bias** (e.g. purely AC-coupled).
- You want to observe the natural **start-up transient** from zero.
- The DC point is **not meaningful** (e.g. oscillator circuits).

## Debugging DC OP Failures

If the DC operating point fails to converge:

1. **Increase source stepping steps:** `source_stepping_steps=20` or `50`.
2. **Increase NR iterations:** `nr_max_iterations=100`.
3. **Check topology:** Ensure no floating nodes, no voltage-source loops.
4. **Add bias resistors:** High-value resistors to ground on floating gate
   nodes (MOSFET circuits commonly need this).
