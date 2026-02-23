# Event Detection

Event detection monitors node voltages during a transient simulation and records when specified conditions are met — zero crossings, threshold crossings, or arbitrary user-defined events.

## Core Classes

### `EventDetector`

The main manager. Create one, register event specifications, attach it to the circuit, and inspect detected events after simulation.

```python
ed = EventDetector()
ed.add(ZeroCrossing(node=n_out, direction="rising"))
ckt.SetEventDetector(ed)
# ... run simulation loop ...
events = ed.events  # list of EventRecord
```

| Method | Description |
|---|---|
| `ed.add(spec)` | Register a `ZeroCrossing`, `ThresholdCrossing`, or `CustomEvent` |
| `ed.on_event(name, callback)` | Register a callback that fires when the named event is detected |
| `ed.clear()` | Reset all recorded events and internal state |
| `ed.events` | Property — returns a list of all `EventRecord` objects detected so far |

### `ZeroCrossing`

Detects when a node voltage crosses zero.

```python
ZeroCrossing(
    node=n_out,           # Node object
    direction="rising",   # "rising", "falling", or "both"
    name=None,            # optional custom event name
)
```

### `ThresholdCrossing`

Detects when a node voltage crosses a specified level.

```python
ThresholdCrossing(
    node=n_out,           # Node object
    level=2.5,            # threshold voltage
    direction="falling",  # "rising", "falling", or "both"
    name=None,            # optional custom event name
)
```

### `CustomEvent`

Detects a user-defined boolean condition transition.

```python
CustomEvent(
    name="saturated",
    trigger=lambda x, ctx: x[vce_index] < 0.2,
    on_rising=True,       # fire when condition becomes True
    on_falling=False,     # fire when condition becomes False
)
```

### `CrossingDirection`

Enum for crossing direction:

```python
class CrossingDirection(Enum):
    RISING = "rising"
    FALLING = "falling"
    BOTH = "both"
```

String values `"rising"`, `"falling"`, and `"both"` are automatically converted to the enum.

### `EventRecord`

Dataclass for each detected event:

```python
@dataclass
class EventRecord:
    time: float       # simulation time (s) when the event occurred
    name: str         # event name
    value: float      # node voltage at the crossing
    direction: str    # "rising" or "falling"
```

## Workflow

1. **Build the circuit** as normal and add probes.
2. **Create an `EventDetector`** and register events.
3. **Attach it** to the circuit with `ckt.SetEventDetector(ed)`.
4. **Finalize** the circuit.
5. **Run the transient loop** with `ckt.Simulate(dt)`.
6. **Inspect** `ed.events` after the simulation completes.

> **Note:** The `EventDetector.check()` method is called automatically after each `Simulate()` step when the detector is attached to a circuit.

## Example — Zero Crossing Detection

```python
from PyEEL import *
import numpy as np

ckt = Circuit(solver=NumpySolver())

nm    = ckt.NodeManager
gnd   = nm.GroundNode
n_out = nm.AddNode("n_out")

ckt.AddComponent(ACVoltageSource("V1", (n_out, gnd),
                                 amplitude=5.0, frequency=1.0))
ckt.AddComponent(Resistor("R1", (n_out, gnd), resistance=1e3))

# Probe
v_out = VoltageProbe("V(n_out)", n_out)
ckt.AddProbe(v_out)

# Event detection — detect rising zero crossings
ed = EventDetector()
ed.add(ZeroCrossing(node=n_out, direction="rising"))
ckt.SetEventDetector(ed)

ckt.Finalize()

# Simulate 2 seconds at 1 ms time step
dt    = 1e-3
t_end = 2.0
steps = int(t_end / dt)
time_array = np.empty(steps)
volt_array = np.empty(steps)

for i in range(steps):
    x = ckt.Simulate(dt)
    time_array[i] = (i + 1) * dt
    volt_array[i] = x[n_out.Index]

# Inspect events
for ev in ed.events:
    print(f"  t = {ev.time:.4f} s | value = {ev.value:+.4f} V | {ev.direction}")

# Plot the transient waveform
plot_transient(time_array, {"V(n_out)": volt_array})
```

A 1 Hz sine completes 2 full cycles in 2 seconds. Expect 2 rising zero crossings (at approximately *t* = 0 s and *t* = 1 s, or wherever the sine crosses zero going positive).

## Using Callbacks

You can register callbacks to react to events in real time:

```python
def on_crossing(ev: EventRecord):
    print(f"[EVENT] {ev.name} at t={ev.time:.4f}s")

ed = EventDetector()
zc = ZeroCrossing(node=n_out, direction="both")
ed.add(zc)
ed.on_event(zc.name, on_crossing)
```

## Combining Multiple Events

Register as many event specifications as needed:

```python
ed = EventDetector()
ed.add(ZeroCrossing(node=n_out, direction="rising"))
ed.add(ThresholdCrossing(node=n_out, level=2.5, direction="falling"))
ed.add(CustomEvent("clipped", lambda x, ctx: abs(x[n_out.Index]) > 4.5))
ckt.SetEventDetector(ed)
```

All events are checked on every simulation step. Access the combined list via `ed.events`, or filter by name:

```python
zero_events = [e for e in ed.events if "zero_crossing" in e.name]
```
