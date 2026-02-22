# Example: Common-Emitter Amplifier

A voltage-divider-biased NPN common-emitter amplifier — the fundamental
transistor amplifier topology.

**File:** `examples/ce_amplifier.py`

## Circuit

```
         Vcc (12 V)
          │
     ┌────┤────┐
     R1   Rc    │
    (56k) (1k)  │
     │    │     │
     ├── Q1 (NPN 2N2222)
     │    │
     R2   Re
    (10k) (220)
     │    │
    GND  GND

    AC input (1 kHz, 20 mV) coupled through C_in
    Output taken from collector through C_out
```

## Code

```python
from PyEEL import (
    Circuit, NumpySolver, SimulationConfig,
    Resistor, Capacitor, NPN,
    DCVoltageSource, ACVoltageSource,
    VoltageProbe, CurrentProbe,
    LivePlotter, LiveSimulation,
)

config = SimulationConfig(dc_operating_point=True)
ckt = Circuit(solver=NumpySolver(), config=config)
nm  = ckt.NodeManager
gnd = nm.GroundNode

n_vcc = nm.AddNode("Vcc")
n_in  = nm.AddNode("in")
n_b   = nm.AddNode("base")
n_c   = nm.AddNode("collector")
n_e   = nm.AddNode("emitter")
n_out = nm.AddNode("out")

# Power supply
ckt.AddComponent(DCVoltageSource("Vcc", (n_vcc, gnd), voltage=12))

# Bias network
ckt.AddComponent(Resistor("R1", (n_vcc, n_b), resistance=56e3))
ckt.AddComponent(Resistor("R2", (n_b, gnd), resistance=10e3))

# Transistor
ckt.AddComponent(NPN("Q1", (n_c, n_b, n_e),
                      Is=14.34e-15, BF=255.9, Vaf=74.03))

# Collector and emitter resistors
ckt.AddComponent(Resistor("Rc", (n_vcc, n_c), resistance=1e3))
ckt.AddComponent(Resistor("Re", (n_e, gnd), resistance=220))

# AC input with coupling capacitors
ckt.AddComponent(ACVoltageSource("Vin", (n_in, gnd), amplitude=0.02, frequency=1000))
ckt.AddComponent(Capacitor("Cin", (n_in, n_b), capacitance=10e-6))
ckt.AddComponent(Capacitor("Cout", (n_c, n_out), capacitance=10e-6))
ckt.AddComponent(Resistor("RL", (n_out, gnd), resistance=10e3))

# Probes
ckt.AddProbe(VoltageProbe("V_in", n_in))
ckt.AddProbe(VoltageProbe("V_out", n_out))
ckt.AddProbe(VoltageProbe("V_base", n_b))
ckt.Finalize()

plotter = LivePlotter(
    [ckt.Probes[0], ckt.Probes[1]],   # input vs output
    [ckt.Probes[2]],                    # base voltage
)
sim = LiveSimulation(ckt, plotter, dt=5e-6, speed=200)
sim.Run()
```

## What to Observe

- The DC operating point sets V_base ≈ 1.8 V, V_collector ≈ 6–8 V.
- The 20 mV input is amplified and **inverted** at the output.
- Voltage gain: $A_v \approx -R_C / R_E \approx -4.5$.
- The coupling caps block DC — the output swings around 0 V.

## Key Concepts Demonstrated

- DC operating-point analysis with BJT
- Voltage-divider biasing
- AC coupling with capacitors
- Non-linear Newton–Raphson convergence
