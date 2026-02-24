"""
PyEEL — Resistor Voltage Divider Noise Analysis
=================================================
Demonstrates noise analysis on a simple resistive voltage divider.

Topology::

    V1 (DC 5 V)
     ├──(n_in)── R1 (10 kΩ) ──(n_out)── R2 (10 kΩ) ──(GND)

Both resistors generate Johnson-Nyquist (thermal) noise.  The noise
analysis computes the output-referred noise spectral density and
the total integrated RMS noise over the bandwidth 10 Hz – 100 kHz.
"""

from PyEEL import *

def main():
    # ── build circuit ───────────────────────────────────────────────
    ckt = Circuit(solver=NumpySolver())

    nm    = ckt.NodeManager
    gnd   = nm.GroundNode
    n_in  = nm.AddNode("n_in")
    n_out = nm.AddNode("n_out")

    ckt.AddComponent(DCVoltageSource("V1", (n_in, gnd), voltage=5.0))
    ckt.AddComponent(Resistor("R1", (n_in, n_out), resistance=10e3))
    ckt.AddComponent(Resistor("R2", (n_out, gnd), resistance=10e3))

    ckt.Finalize()

    # ── run noise analysis ──────────────────────────────────────────
    assert n_out.Index is not None
    noise_result = ckt.RunNoise(
        10.0, 100e3, 200,
        output_node_index=n_out.Index,
    )

    # ── print results ───────────────────────────────────────────────
    print(f"Integrated RMS noise : {noise_result.integrated_noise_vrms * 1e6:.2f} µV")
    print(f"Frequency range      : {noise_result.frequencies[0]:.0f} Hz – "
          f"{noise_result.frequencies[-1]:.0f} Hz")

    if noise_result.component_contributions:
        mid = len(noise_result.frequencies) // 2
        print(f"\nPer-component noise contributions (at {noise_result.frequencies[mid]:.0f} Hz):")
        for name, contrib in noise_result.component_contributions.items():
            print(f"  {name}: {contrib[mid]:.4e} V²/Hz")

    # ── plot noise spectrum ─────────────────────────────────────────
    plot_noise_spectrum(noise_result)


if __name__ == "__main__":
    main()
