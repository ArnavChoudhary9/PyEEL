# Example: Linear Power Supply

A complete mains-powered linear power supply: transformer step-down →
full-bridge rectifier → capacitor filter → resistive load.

**File:** `examples/linear_power_supply.py`

## Circuit

```
AC Mains         Transformer        Bridge Rectifier      Filter    Load
(240V 50Hz) ──── 20:1 step-down ──── 4× Diode bridge ──── 1000µF ── 100Ω
                 (100H → 0.25H)                           │
                                                         GND
```

## Code Highlights

```python
config = SimulationConfig(
    dc_operating_point=True,
    source_stepping_steps=20,    # more ramp steps for this large circuit
    nr_max_iterations=100,
)
ckt = Circuit(solver=NumpySolver(), config=config)
nm  = ckt.NodeManager
gnd = nm.GroundNode

n_pri = nm.AddNode("primary")
n_sec = nm.AddNode("secondary")
n_dc  = nm.AddNode("dc_out")

# 240 V RMS → 339 V peak
ckt.AddComponent(ACVoltageSource("Vmains", (n_pri, gnd),
                                 amplitude=339.4, frequency=50))

# Step-down transformer: 240 V → 12 V
T1 = Transformer("T1", (n_pri, gnd), (n_sec, gnd),
                 primary_inductance=100, secondary_inductance=0.25, k=0.999)
ckt.AddComponent(T1)

# Full bridge (4 diodes)
ckt.AddComponent(Diode("D1", (n_sec, n_dc)))
ckt.AddComponent(Diode("D2", (gnd, n_dc)))
ckt.AddComponent(Diode("D3", (gnd, n_sec)))   # reverse path
ckt.AddComponent(Diode("D4", (n_dc_neg, n_sec)))  # (simplified)

# Filter + load
ckt.AddComponent(Capacitor("C1", (n_dc, gnd), capacitance=1000e-6))
ckt.AddComponent(Resistor("RL", (n_dc, gnd), resistance=100))
```

## What to Observe

- The secondary shows a ~17 V peak sine (12 V RMS).
- The bridge rectifier produces full-wave rectified pulses.
- The filter capacitor smooths the output to ~15 V DC with ripple.
- Increasing the load resistance reduces ripple.

## Key Concepts Demonstrated

- Transformer coupling and turns ratio
- Full-bridge rectifier with 4 diodes
- Capacitor filtering and ripple
- Source stepping for robust DC operating point convergence
- `speed=200` to fast-forward through start-up
