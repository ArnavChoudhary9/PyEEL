# Example: Event Detection — Zero Crossings

This example demonstrates transient simulation with the `EventDetector` to capture rising zero crossings of a sinusoidal signal.

## Circuit

```
V1 (AC 5 V, 1 Hz)
 ├──(n_out)── R1 (1 kΩ) ──(GND)
```

A 1 Hz sine wave drives a load resistor. Over 2 seconds of simulation, the signal completes 2 full cycles and the rising zero crossings are recorded.

## Full Code

```python
from PyEEL import *
import numpy as np

def main():
    # ── Build circuit ───────────────────────────────────────────────
    ckt = Circuit(solver=NumpySolver())

    nm    = ckt.NodeManager
    gnd   = nm.GroundNode
    n_out = nm.AddNode("n_out")

    ckt.AddComponent(ACVoltageSource("V1", (n_out, gnd),
                                     amplitude=5.0, frequency=1.0))
    ckt.AddComponent(Resistor("R1", (n_out, gnd), resistance=1e3))

    # ── Probes ──────────────────────────────────────────────────────
    v_out = VoltageProbe("V(n_out)", n_out)
    ckt.AddProbe(v_out)

    # ── Event detection ─────────────────────────────────────────────
    ed = EventDetector()
    ed.add(ZeroCrossing(node=n_out, direction="rising"))
    ckt.SetEventDetector(ed)

    ckt.Finalize()

    # ── Transient simulation ────────────────────────────────────────
    dt    = 1e-3   # 1 ms time step
    t_end = 2.0    # simulate 2 seconds

    steps = int(t_end / dt)
    time_array = np.empty(steps)
    volt_array = np.empty(steps)

    for i in range(steps):
        x = ckt.Simulate(dt)
        time_array[i] = (i + 1) * dt
        volt_array[i] = x[n_out.Index]

    # ── Print detected events ───────────────────────────────────────
    events = ed.events
    print(f"Detected {len(events)} rising zero-crossing event(s):\n")
    for ev in events:
        print(f"  t = {ev.time:.4f} s  |  value = {ev.value:+.4f} V  |  {ev.direction}")

    # ── Plot transient waveform ─────────────────────────────────────
    plot_transient(time_array, {"V(n_out)": volt_array})

if __name__ == "__main__":
    main()
```

## Step-by-Step Walkthrough

1. **Build a simple circuit** — an AC voltage source (5 V amplitude, 1 Hz) drives a 1 kΩ load.
2. **Add a voltage probe** to record the output node voltage.
3. **Create an `EventDetector`** and register a `ZeroCrossing` on `n_out` with `direction="rising"`.
4. **Attach the detector** to the circuit with `ckt.SetEventDetector(ed)`.
5. **Finalize** the circuit.
6. **Run the transient loop** — 2000 steps of 1 ms each, storing time and voltage arrays.
7. **Inspect events** — `ed.events` contains an `EventRecord` for each rising zero crossing.
8. **Plot** — `plot_transient()` shows the full sinusoidal waveform.

## Expected Output

```
Detected 2 rising zero-crossing event(s):

  t = 0.0010 s  |  value = +0.0314 V  |  rising
  t = 1.0010 s  |  value = +0.0314 V  |  rising
```

The two events correspond to the sine wave crossing zero in the positive direction — once near *t* = 0 s and again near *t* = 1 s (one period later).

The transient plot shows the 5 V, 1 Hz sine wave over the 2-second window. The detected crossing times align with the positive-going zero crossings visible on the waveform.

## Variations

- Use `direction="both"` to capture both rising and falling crossings (expect 4 events over 2 seconds).
- Use `ThresholdCrossing(node=n_out, level=2.5, direction="falling")` to detect when the signal drops below 2.5 V.
- Register callbacks with `ed.on_event(name, callback)` for real-time event processing during simulation.
