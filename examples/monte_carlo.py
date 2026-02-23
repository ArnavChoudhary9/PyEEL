"""
PyEEL — Monte Carlo Analysis of a Voltage Divider
===================================================
Demonstrates Monte Carlo analysis with component tolerances.

Topology::

    V1 (DC 10 V)
     ├──(n_in)── R1 (10 kΩ ± 5%) ──(n_out)── R2 (10 kΩ ± 5%) ──(GND)

With nominal values the output voltage is 5.0 V.  Both resistors
have ±5 % manufacturing tolerance.  The Monte Carlo simulation
runs 500 random trials to determine the statistical distribution
of the output voltage.
"""

from PyEEL import *

def main():
    # ── build circuit ───────────────────────────────────────────────
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

    # ── define measurement function ─────────────────────────────────
    def measure_vout(circuit, x_dc):
        """Extract output node voltage from the DC solution."""
        return x_dc[n_out.Index]

    # ── run Monte Carlo ─────────────────────────────────────────────
    mc_result = ckt.RunMonteCarlo(
        tolerances=[
            (r1, "Resistance", Tolerance.percent(5)),
            (r2, "Resistance", Tolerance.percent(5)),
        ],
        num_runs=500,
        measure=measure_vout,
        seed=42,
    )

    # ── print statistics ────────────────────────────────────────────
    print(f"Monte Carlo Analysis — {mc_result.num_runs} runs")
    print(f"  Mean   : {mc_result.mean:.4f} V")
    print(f"  Std    : {mc_result.std:.4f} V")
    print(f"  Min    : {mc_result.min:.4f} V")
    print(f"  Max    : {mc_result.max:.4f} V")
    print(f"  5th %  : {mc_result.percentile_5:.4f} V")
    print(f"  95th % : {mc_result.percentile_95:.4f} V")

    # ── plot histogram ──────────────────────────────────────────────
    plot_monte_carlo(mc_result)


if __name__ == "__main__":
    main()
