"""
PyEEL — Parameter Sweep of a Voltage Divider
==============================================
Demonstrates parameter sweep by varying R1 in a voltage divider
and observing the DC output voltage.

Topology::

    V1 (DC 10 V)
     ├──(n_in)── R1 (swept 1 kΩ → 100 kΩ) ──(n_out)── R2 (10 kΩ) ──(GND)

With R2 fixed at 10 kΩ, the output voltage follows:

    V_out = V1 · R2 / (R1 + R2)

As R1 increases from 1 kΩ to 100 kΩ the output drops from
~9.09 V down to ~0.91 V.
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

    # ── run parameter sweep ─────────────────────────────────────────
    sweep_result = ckt.RunSweep(
        parameters=[
            (r1, "Resistance", 1e3, 100e3, 20),
        ],
        measure=measure_vout,
    )

    # ── print a few sample points ───────────────────────────────────
    r_values = sweep_result.sweep_values["R1.Resistance"]
    v_values = sweep_result.measured

    print("R1 (Ω)        V_out (V)")
    print("─" * 30)
    for i in range(0, len(r_values), 4):
        print(f"  {r_values[i]:>9.0f}    {v_values[i]:.4f}")

    # ── plot sweep ──────────────────────────────────────────────────
    plot_sweep(sweep_result)


if __name__ == "__main__":
    main()
