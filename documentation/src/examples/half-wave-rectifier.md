# Example: Half-Wave Rectifier

A simple half-wave rectifier converts AC to pulsating DC using a single
diode.

**File:** `examples/half_wave_rectifier.py`

## Circuit

```
        D1 (1N4007)
n1 ──────►|────── n2
│                  │
V_ac             R_load
(5V 50Hz)        (1 kΩ)
│                  │
GND ──────────── GND
```

## Code

```python
from PyEEL import (
    Circuit, NumpySolver, SimulationConfig,
    Resistor, Diode, ACVoltageSource,
    VoltageProbe, CurrentProbe,
    LivePlotter, LiveSimulation,
)

config = SimulationConfig(dc_operating_point=True)
ckt = Circuit(solver=NumpySolver(), config=config)
nm  = ckt.NodeManager
gnd = nm.GroundNode

n1 = nm.AddNode("n1")
n2 = nm.AddNode("n2")

ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=5, frequency=50))
ckt.AddComponent(d1 := Diode("D1", (n1, n2), Is=7.02e-9, n=1.77))
ckt.AddComponent(Resistor("R1", (n2, gnd), resistance=1000))

ckt.AddProbe(VoltageProbe("V_in", n1))
ckt.AddProbe(VoltageProbe("V_out", n2))
ckt.AddProbe(CurrentProbe("I_D1", d1))
ckt.Finalize()

plotter = LivePlotter(
    [ckt.Probes[0], ckt.Probes[1]],   # voltages
    [ckt.Probes[2]],                    # diode current
)
sim = LiveSimulation(ckt, plotter, dt=1e-4, speed=100)
sim.Run()
```

## What to Observe

- **V_out** follows V_in during positive half-cycles (minus ~0.7 V diode drop).
- During negative half-cycles, the diode blocks and V_out ≈ 0.
- The diode current flows only during conduction.

## Key Concepts Demonstrated

- Non-linear device (Diode) with Newton–Raphson
- AC voltage source
- Voltage and current probes
- Live plotting with multiple subplots
