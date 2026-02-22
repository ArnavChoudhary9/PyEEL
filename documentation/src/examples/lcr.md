# Example: Series LCR Circuit

A series inductor-capacitor-resistor circuit driven at resonance,
demonstrating energy exchange and voltage magnification.

**File:** `examples/lcr.py`

## Circuit

```
V_ac ──── L (0.1H) ──── C (0.01F) ──── R (1Ω) ──── GND
(5V, 5Hz)
```

## Parameters

- $f_0 = \dfrac{1}{2\pi\sqrt{LC}} = \dfrac{1}{2\pi\sqrt{0.1 \times 0.01}} \approx 5.03$ Hz
- $Q = \dfrac{1}{R}\sqrt{\dfrac{L}{C}} = \sqrt{\dfrac{0.1}{0.01}} \approx 3.16$
- At resonance, $V_C = Q \times V_{source} \approx 15.8$ V peak

## Code

```python
from PyEEL import *

ckt = Circuit(solver=NumpySolver())
nm  = ckt.NodeManager
gnd = nm.GroundNode

n1 = nm.AddNode("n1")
n2 = nm.AddNode("n2")
n3 = nm.AddNode("n3")

ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=5, frequency=5))
ckt.AddComponent(L1 := Inductor("L1", (n1, n2), inductance=0.1))
ckt.AddComponent(Capacitor("C1", (n2, n3), capacitance=0.01))
ckt.AddComponent(Resistor("R1", (n3, gnd), resistance=1))

ckt.AddProbe(VoltageProbe("V_source", n1))
ckt.AddProbe(VoltageProbe("V_L", n1, n2))
ckt.AddProbe(VoltageProbe("V_C", n2, n3))
ckt.AddProbe(CurrentProbe("I", L1))
ckt.Finalize()

plotter = LivePlotter(
    [ckt.Probes[0], ckt.Probes[1], ckt.Probes[2]],   # voltages
    [ckt.Probes[3]],                                    # current
    window=1.0,
)
sim = LiveSimulation(ckt, plotter, dt=0.0005, speed=60)
sim.Run()
```

## What to Observe

- The capacitor and inductor voltages are **180° out of phase** at resonance.
- $V_C$ peaks at $Q$ times the source voltage.
- The current is **in phase** with the source at resonance (impedance is
  purely resistive).
- Energy oscillates between the inductor (magnetic) and capacitor (electric).

## Key Concepts Demonstrated

- Inductor and capacitor transient companion models
- Resonance and quality factor
- Differential voltage probes (`VoltageProbe("V_L", n1, n2)`)
- Current probes on inductors
