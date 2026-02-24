"""
PyEEL — Harmonic Balance Analysis of a Diode Clipper
======================================================
Demonstrates harmonic balance to find the periodic steady state
of a nonlinear circuit driven by a single tone.

Topology::

    V1 (AC 2 V, 1 kHz)
     ├──(n_in)── R1 (1 kΩ) ──(n_out)── D1 (anode=n_out, cathode=GND)
                                   │
                              R_load (10 kΩ) ──(GND)

The series resistor and shunt diode form a simple clipper.  On
positive half-cycles the diode conducts, clamping V(n_out) near
+0.7 V; on negative half-cycles D1 is off and V(n_out) follows
the source through the R1 / R_load divider.

Because the diode clips the waveform, the output contains
significant harmonic content.  Harmonic Balance finds the
steady-state spectrum directly without long transient simulation.
"""

from PyEEL import *

def main():
    # ── simulation config ───────────────────────────────────────────
    config = SimulationConfig(
        dc_operating_point=True,
        gmin=1e-12,
    )

    # ── build circuit ───────────────────────────────────────────────
    ckt = Circuit(solver=NumpySolver(), config=config)

    nm    = ckt.NodeManager
    gnd   = nm.GroundNode
    n_in  = nm.AddNode("n_in")
    n_out = nm.AddNode("n_out")

    ckt.AddComponent(ACVoltageSource("V1", (n_in, gnd),
                                     amplitude=2.0, frequency=1000.0))
    ckt.AddComponent(Resistor("R1", (n_in, n_out), resistance=1e3))
    ckt.AddComponent(Diode("D1", (n_out, gnd)))
    ckt.AddComponent(Resistor("R_load", (n_out, gnd), resistance=10e3))

    ckt.Finalize()

    # ── run harmonic balance ────────────────────────────────────────
    hb_result = ckt.RunHarmonicBalance(
        fundamental=1000.0,
        num_harmonics=7,
    )

    # ── print convergence info ──────────────────────────────────────
    print(f"Converged : {hb_result.converged}")
    print(f"Iterations: {hb_result.iterations}")
    print(f"Residual  : {hb_result.residual:.2e}")
    print(f"\nHarmonic spectrum at n_out (fundamental = {hb_result.fundamental} Hz):")

    # spectrum is (K+1, N) — select the output node column
    node_spectrum = abs(hb_result.spectrum[:, n_out.Index])
    for i, (freq, mag) in enumerate(zip(hb_result.frequencies,
                                        node_spectrum)):
        label = "DC" if i == 0 else f"H{i}"
        print(f"  {label:>3s}  {freq:>10.0f} Hz   {mag:.4f} V")

    # ── plot harmonic spectrum ──────────────────────────────────────
    assert n_out.Index is not None
    plot_harmonic_spectrum(hb_result, node_index=n_out.Index)


if __name__ == "__main__":
    main()
