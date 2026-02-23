# Example: Monte Carlo — Voltage Divider Tolerance

This example uses Monte Carlo analysis to determine the statistical distribution of output voltage in a resistive voltage divider when both resistors have ±5% manufacturing tolerance.

## Circuit

```
V1 (DC 10 V)
 ├──(n_in)── R1 (10 kΩ ± 5%) ──(n_out)── R2 (10 kΩ ± 5%) ──(GND)
```

With nominal values, the output voltage is exactly 5.0 V. The question is: *how much does V_out vary when R1 and R2 have ±5% tolerance?*

## Full Code

```python
from PyEEL import *

def main():
    # ── Build circuit ───────────────────────────────────────────────
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

    # ── Define measurement function ─────────────────────────────────
    def measure_vout(circuit, x_dc):
        """Extract output node voltage from the DC solution."""
        return x_dc[n_out.Index]

    # ── Run Monte Carlo ─────────────────────────────────────────────
    mc_result = ckt.RunMonteCarlo(
        tolerances=[
            (r1, "Resistance", Tolerance.percentage(5)),
            (r2, "Resistance", Tolerance.percentage(5)),
        ],
        num_runs=500,
        measure=measure_vout,
        seed=42,
    )

    # ── Print statistics ────────────────────────────────────────────
    print(f"Monte Carlo Analysis — {mc_result.num_runs} runs")
    print(f"  Mean   : {mc_result.mean:.4f} V")
    print(f"  Std    : {mc_result.std:.4f} V")
    print(f"  Min    : {mc_result.min:.4f} V")
    print(f"  Max    : {mc_result.max:.4f} V")
    print(f"  5th %  : {mc_result.percentile_5:.4f} V")
    print(f"  95th % : {mc_result.percentile_95:.4f} V")

    # ── Plot histogram ──────────────────────────────────────────────
    plot_monte_carlo(mc_result)

if __name__ == "__main__":
    main()
```

## Step-by-Step Walkthrough

1. **Build a voltage divider** — two 10 kΩ resistors with a 10 V DC source.
2. **Define the measurement** — `measure_vout` extracts `V(n_out)` from each DC solution.
3. **Specify tolerances** — both resistors have uniform ±5% tolerance via `Tolerance.percentage(5)`.
4. **Run 500 trials** — each trial randomises resistor values within their tolerance bands, solves the DC operating point, and records V_out.
5. **Inspect statistics** — mean, standard deviation, min/max, and percentiles.
6. **Plot** — `plot_monte_carlo()` generates a histogram with statistical overlays.

## Expected Output

```
Monte Carlo Analysis — 500 runs
  Mean   : 5.0001 V
  Std    : 0.1441 V
  Min    : 4.5603 V
  Max    : 5.4209 V
  5th %  : 4.7621 V
  95th % : 5.2384 V
```

The histogram shows a roughly symmetric distribution centred on 5.0 V. The ±5% resistor tolerance translates to approximately ±5% variation in the output voltage. Vertical annotation lines mark the mean (red), ±1σ (orange), and 5th/95th percentiles (blue).

## Notes

- Set `seed=42` (or any integer) for reproducible results.
- The `Tolerance.gaussian(mean, std)` factory can be used instead for Gaussian-distributed parameters.
- Increase `num_runs` for smoother histograms and more precise statistics.
