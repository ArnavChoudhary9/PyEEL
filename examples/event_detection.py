"""
PyEEL — Event Detection (Zero-Crossing) During Transient Simulation
=====================================================================
Demonstrates the EventDetector to capture zero crossings of
a sinusoidal signal during a transient simulation.

Topology::

    V1 (AC 5 V, 1 Hz)
     ├──(n_out)── R1 (1 kΩ) ──(GND)

The 1 Hz sine drives a load resistor.  An EventDetector records
every rising zero crossing of the output node over 2 seconds.
A 1 Hz signal has 2 rising zero crossings in 2 seconds.
"""

from PyEEL import *
import numpy as np

def main():
    # ── build circuit ───────────────────────────────────────────────
    ckt = Circuit(solver=NumpySolver())

    nm    = ckt.NodeManager
    gnd   = nm.GroundNode
    n_out = nm.AddNode("n_out")

    ckt.AddComponent(ACVoltageSource("V1", (n_out, gnd),
                                     amplitude=5.0, frequency=1.0))
    ckt.AddComponent(Resistor("R1", (n_out, gnd), resistance=1e3))

    # ── probes ──────────────────────────────────────────────────────
    v_out = VoltageProbe("V(n_out)", n_out)
    ckt.AddProbe(v_out)

    # ── event detection ─────────────────────────────────────────────
    ed = EventDetector()
    ed.add(ZeroCrossing(node=n_out, direction="rising"))
    ckt.SetEventDetector(ed)

    ckt.Finalize()

    # ── transient simulation ────────────────────────────────────────
    dt    = 1e-3   # 1 ms time step
    t_end = 2.0    # simulate 2 seconds

    steps = int(t_end / dt)
    time_array = np.empty(steps)
    volt_array = np.empty(steps)

    for i in range(steps):
        x = ckt.Simulate(dt)
        time_array[i] = (i + 1) * dt
        volt_array[i] = x[n_out.Index]

    # ── print detected events ───────────────────────────────────────
    events = ed.events
    print(f"Detected {len(events)} rising zero-crossing event(s):\n")
    for ev in events:
        print(f"  t = {ev.time:.4f} s  |  value = {ev.value:+.4f} V  |  {ev.direction}")

    # ── plot transient waveform ─────────────────────────────────────
    plot_transient(time_array, {"V(n_out)": volt_array})


if __name__ == "__main__":
    main()
