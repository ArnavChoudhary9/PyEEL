# Probes

Probes record simulation data (voltages and currents) at each time step
for later plotting or analysis.

```python
from PyEEL import VoltageProbe, CurrentProbe
```

## Creating Probes

### Voltage Probe

```python
VoltageProbe(name: str, *nodes: Node) -> Probe
```

Measures the voltage between one or two nodes:

```python
# Voltage at a node (relative to GND)
v_out = VoltageProbe("V_out", n_out)

# Voltage across two nodes (V_a − V_b)
v_ab = VoltageProbe("V_ab", n_a, n_b)
```

### Current Probe

```python
CurrentProbe(name: str, component: Component) -> Probe
```

Measures the branch current through a component that has an **auxiliary
unknown** (voltage sources, inductors, dependent sources with sense elements):

```python
i_v1 = CurrentProbe("I_V1", v1_source)
i_L1 = CurrentProbe("I_L1", L1_inductor)
```

## Registering Probes

```python
ckt.AddProbe(v_out)
ckt.AddProbe(i_v1)
```

Probes must be added **before** `Finalize()`.

## Accessing Data

After simulation, each probe stores time-stamped data:

| Property | Type | Description |
|---|---|---|
| `TimeData` | `list[float]` | Time values (seconds) |
| `ValueData` | `list[float]` | Measured values (V or A) |
| `Name` | `str` | Probe name |
| `Type` | `ProbeType` | `VOLTAGE` or `CURRENT` |

```python
import matplotlib.pyplot as plt

plt.plot(v_out.TimeData, v_out.ValueData)
plt.xlabel("Time (s)")
plt.ylabel("Voltage (V)")
plt.show()
```

## Methods

| Method | Description |
|---|---|
| `Record(time, solution)` | Record a data point (called automatically by `Circuit.Simulate`) |
| `Clear()` | Clear all recorded data |
| `Print()` | Print the last few data points to console |
| `Save(file_path=None)` | Save data to a CSV file |
| `Plot(window=None)` | Quick matplotlib plot |

## `ProbeType` Enum

| Value | Description |
|---|---|
| `VOLTAGE` | Voltage measurement |
| `CURRENT` | Current measurement |

## The `Probe` Constructor (Advanced)

```python
Probe(name: str, probe_type: ProbeType, *nodes: Node,
      component: Component | None = None)
```

The `VoltageProbe` and `CurrentProbe` factories are preferred, but you
can create a Probe directly if needed.
