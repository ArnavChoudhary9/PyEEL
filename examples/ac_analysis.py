"""
PyEEL — RC Low-Pass Filter AC Analysis
========================================
Demonstrates AC frequency sweep and Bode plot generation.

Topology::

    V1 (AC 1 V)
     ├──(n_in)── R1 (1 kΩ) ──(n_out)── C1 (100 nF) ──(GND)

This is a first-order RC low-pass filter.
The theoretical -3 dB frequency is:

    f_c = 1 / (2π·R·C) = 1 / (2π · 1 kΩ · 100 nF) ≈ 1592 Hz

The AC sweep runs from 1 Hz to 1 MHz and the resulting Bode plot
shows the magnitude roll-off and phase shift.
"""

from PyEEL import *
import numpy as np

def main():
    # ── build circuit ───────────────────────────────────────────────
    ckt = Circuit(solver=NumpySolver())

    nm    = ckt.NodeManager
    gnd   = nm.GroundNode
    n_in  = nm.AddNode("n_in")
    n_out = nm.AddNode("n_out")

    v1 = ACVoltageSource("V1", (n_in, gnd), amplitude=1.0, frequency=1000.0)
    r1 = Resistor("R1", (n_in, n_out), resistance=1e3)
    c1 = Capacitor("C1", (n_out, gnd), capacitance=100e-9)

    ckt.AddComponent(v1)
    ckt.AddComponent(r1)
    ckt.AddComponent(c1)

    ckt.Finalize()

    # ── run AC analysis ─────────────────────────────────────────────
    ac_result = ckt.RunAC(
        1.0, 1e6, 200,
        input_source_name="V1",
        output_node_index=n_out.Index,
    )

    # ── find -3 dB frequency ────────────────────────────────────────
    idx_3dB = np.argmin(np.abs(ac_result.magnitude_dB - (-3.0)))
    f_3dB = ac_result.frequencies[idx_3dB]

    R, C = 1e3, 100e-9
    f_theory = 1.0 / (2.0 * np.pi * R * C)

    print(f"Measured -3 dB frequency : {f_3dB:.1f} Hz")
    print(f"Theoretical -3 dB freq  : {f_theory:.1f} Hz")

    # ── plot Bode diagram ───────────────────────────────────────────
    plot_bode(ac_result)


if __name__ == "__main__":
    main()
