# Example: AC Analysis — RC Low-Pass Filter

This example demonstrates AC small-signal analysis on a first-order RC low-pass filter and produces a Bode plot showing magnitude and phase response.

## Circuit

```
V1 (AC 1 V)
 ├──(n_in)── R1 (1 kΩ) ──(n_out)── C1 (100 nF) ──(GND)
```

The theoretical −3 dB cutoff frequency is:

$$f_c = \frac{1}{2\pi R C} = \frac{1}{2\pi \cdot 1\,\text{k}\Omega \cdot 100\,\text{nF}} \approx 1592\,\text{Hz}$$

## Full Code

```python
from PyEEL import *
import numpy as np

def main():
    # ── Build circuit ───────────────────────────────────────────────
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

    # ── Run AC analysis ─────────────────────────────────────────────
    ac_result = ckt.RunAC(
        1.0, 1e6, 200,
        input_source_name="V1",
        output_node_index=n_out.Index,
    )

    # ── Find −3 dB frequency ────────────────────────────────────────
    idx_3dB = np.argmin(np.abs(ac_result.magnitude_dB - (-3.0)))
    f_3dB = ac_result.frequencies[idx_3dB]

    R, C = 1e3, 100e-9
    f_theory = 1.0 / (2.0 * np.pi * R * C)

    print(f"Measured −3 dB frequency : {f_3dB:.1f} Hz")
    print(f"Theoretical −3 dB freq  : {f_theory:.1f} Hz")

    # ── Plot Bode diagram ───────────────────────────────────────────
    plot_bode(ac_result)

if __name__ == "__main__":
    main()
```

## Step-by-Step Walkthrough

1. **Create the circuit** with a `NumpySolver` backend.
2. **Add nodes** — `n_in` for the input, `n_out` for the output, and the implicit ground.
3. **Add components** — an AC voltage source (1 V amplitude, 1 kHz), a 1 kΩ resistor, and a 100 nF capacitor.
4. **Finalize** the circuit to freeze the topology and allocate MNA arrays.
5. **Run AC analysis** — sweep 200 logarithmically-spaced points from 1 Hz to 1 MHz. The solver linearises the circuit at its DC operating point, builds the complex admittance matrix at each frequency, and extracts the transfer function.
6. **Post-process** — find the frequency closest to −3 dB in the magnitude array.
7. **Plot** — `plot_bode()` produces a two-panel Bode diagram.

## Expected Output

```
Measured −3 dB frequency : 1592.3 Hz
Theoretical −3 dB freq  : 1591.5 Hz
```

The Bode plot shows:

- **Magnitude** — flat at 0 dB below cutoff, rolling off at −20 dB/decade above cutoff (characteristic of a first-order filter).
- **Phase** — starts at 0°, passes through −45° at cutoff, and approaches −90° at high frequencies.
