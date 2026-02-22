# Example: Zener Regulator

A half-wave rectifier feeding a shunt Zener regulator to produce a
regulated ~5.1 V DC from an AC source.

**File:** `examples/zener_regulator.py`

## Circuit

```
V_ac ──►|── D1 ──┬── C_filter ──┬── R_series ──┬── V_out
(12V    (rect)   │   (470 µF)   │   (470 Ω)    │
 50Hz)           │              │               DZ (5.1V)
                GND            GND              │    RL
                                                │   (2k)
                                               GND
```

## Code

```python
from PyEEL import (
    Circuit, NumpySolver, SimulationConfig,
    Resistor, Capacitor, Diode, ZenerDiode,
    ACVoltageSource,
    VoltageProbe, CurrentProbe,
    LivePlotter, LiveSimulation,
)

config = SimulationConfig(dc_operating_point=True)
ckt = Circuit(solver=NumpySolver(), config=config)
nm  = ckt.NodeManager
gnd = nm.GroundNode

n_ac   = nm.AddNode("ac")
n_rect = nm.AddNode("rect")
n_out  = nm.AddNode("out")

# AC source
ckt.AddComponent(ACVoltageSource("Vac", (n_ac, gnd), amplitude=12, frequency=50))

# Rectifier + filter
ckt.AddComponent(Diode("D1", (n_ac, n_rect), Is=7.02e-9, n=1.77))
ckt.AddComponent(Capacitor("C1", (n_rect, gnd), capacitance=470e-6))

# Zener regulator
ckt.AddComponent(Resistor("Rs", (n_rect, n_out), resistance=470))
ckt.AddComponent(dz := ZenerDiode("DZ1", (gnd, n_out), Vz=5.1))
ckt.AddComponent(Resistor("RL", (n_out, gnd), resistance=2000))

# Probes
ckt.AddProbe(VoltageProbe("V_unreg", n_rect))
ckt.AddProbe(VoltageProbe("V_reg", n_out))
ckt.AddProbe(CurrentProbe("I_zener", dz))
ckt.Finalize()

plotter = LivePlotter(
    [ckt.Probes[0], ckt.Probes[1]],
    [ckt.Probes[2]],
)
sim = LiveSimulation(ckt, plotter, dt=2e-4, speed=50)
sim.Run()
```

## What to Observe

- **V_unreg** shows the rectified + filtered waveform (~11 V with ripple).
- **V_reg** is clamped at ~5.1 V by the Zener diode.
- The Zener current varies to absorb excess current from the series resistor.

## Key Concepts Demonstrated

- Zener diode reverse breakdown regulation
- Capacitor filtering
- Half-wave rectification
- Multiple non-linear devices converging together
