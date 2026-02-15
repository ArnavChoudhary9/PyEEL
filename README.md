# PyEEL

**P**ython **E**lectrical **E**ngineering **L**ibrary — A fast, interactive circuit simulator with real-time visualization.

PyEEL implements **Modified Nodal Analysis (MNA)** — the same technique used in SPICE — to solve linear electrical circuits in the time domain. It's designed for education, prototyping, and interactive exploration of circuit dynamics.

---

## Features

- **Real-time Simulation** — ~90,000 time-steps/second for typical circuits
- **Live Plotting** — Non-blocking matplotlib visualization with windowed display
- **Interactive Control** — Pause/resume simulation with spacebar
- **SPICE-like API** — Familiar workflow: build circuit, add probes, simulate
- **Pure Python** — Clean, readable codebase built on NumPy

### Supported Components

| Component       | Type           | Implementation           |
|-----------------|----------------|--------------------------|
| Resistor        | Passive        | Conductance stamp        |
| Capacitor       | Energy storage | Backward-Euler companion |
| Inductor        | Energy storage | Backward-Euler companion |
| Voltage Source  | Excitation     | AC/DC with waveforms     |

---

## Installation

### Prerequisites

- Python 3.10+
- NumPy
- Matplotlib

### Setup

```bash
git clone https://github.com/ArnavChoudhary9/PyEEL.git
cd PyEEL
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Quick Start

```python
from PyEEL import *
from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.Components import Resistor, Capacitor, Inductor
from PyEEL.Components.Sources.VoltageSource import ACVoltageSource
from PyEEL.Probe import VoltageProbe, CurrentProbe
from PyEEL.LivePlotter import LivePlotter
from PyEEL.LiveSimulation import LiveSimulation

# Build circuit
ckt = Circuit(solver=NumpySolver())
nm = ckt.NodeManager
gnd = nm.GroundNode
n1 = nm.AddNode("n1")
n2 = nm.AddNode("n2")

# Add components
ckt.AddComponent(ACVoltageSource("V1", (n1, gnd), amplitude=5.0, frequency=60))
ckt.AddComponent(Resistor("R1", (n1, n2), resistance=100))
ckt.AddComponent(Capacitor("C1", (n2, gnd), capacitance=1e-6))

# Add probes
v_out = VoltageProbe("V(n2)", n2)
ckt.AddProbe(v_out)
ckt.Finalize()

# Run with live plotting
plotter = LivePlotter([v_out], window=0.05)
sim = LiveSimulation(ckt, plotter, dt=1e-5, speed=60)
sim.Run()  # Press Space to pause/resume, close window to stop
```

---

## Example: Series LCR Resonant Circuit

The included [main.py](main.py) demonstrates a series LCR circuit driven at its resonant frequency:

```plaintext
V₁ (5V @ 5Hz) ──[n1]── L₁ (0.1H) ──[n2]── C₁ (0.01F) ──[n3]── R₁ (1Ω) ──[GND]
```

**Characteristics:**

- Resonant frequency: f₀ = 1/(2π√LC) ≈ 5.03 Hz
- Quality factor: Q = (1/R)√(L/C) ≈ 3.16
- Plots voltages at each node and currents through components

Run it:

```bash
python main.py
```

![Example simulation output showing voltage and current waveforms]

---

## Performance

PyEEL is optimized for **real-time interactive circuits**. Key optimizations:

| Technique                     | Impact          |
|-------------------------------|-----------------|
| Batched simulation steps      | **60× speedup** |
| Sliced array conversion       | O(N)→O(window)  |
| Pre-allocated MNA matrices    | ~10% faster     |
| Reused context objects        | ~5% faster      |
| Cached conductances           | ~5% faster      |

**Benchmark** (4×4 system, 2000 steps):  
~90,000 steps/second on a typical laptop (2024 i5, 16GB RAM)

See [Simulation.md](Simulation.md) for detailed performance analysis.

---

## Architecture

```plaintext
PyEEL/
├── Circuit.py          # Top-level simulation controller
├── Node.py             # Circuit nodes (voltage unknowns)
├── NodeManager.py      # Node registry + auxiliary unknowns
├── SimulationContext.py# Immutable time-step metadata
├── Probe.py            # Voltage/current measurement
├── LivePlotter.py      # Real-time matplotlib visualization
├── LiveSimulation.py   # Simulation loop with pause/resume
├── Components/
│   ├── Component.py    # Abstract base for all components
│   ├── Resistor.py     # Conductance stamping
│   ├── Capacitor.py    # Backward-Euler model
│   ├── Inductor.py     # Backward-Euler model
│   └── Sources/
│       ├── VoltageSource.py  # AC/DC voltage sources
│       └── Waveform.py       # Sine/square/triangle/DC
└── Solver/
    └── Solver.py       # Linear solver interface (numpy.linalg.solve)
```

---

## Documentation

- **[Simulation.md](Simulation.md)** — Mathematical deep-dive into MNA, stamping, and time-stepping
- **Inline Docstrings** — All classes and methods are documented

---

## Extending PyEEL

### Add a Custom Component

```python
from PyEEL.Components.Component import Component
import numpy as np

class MyComponent(Component):
    def RegisterUnknowns(self, nodeManager):
        # Request auxiliary unknowns if needed
        pass
    
    def Stamp(self, A, b, context):
        # Add your constitutive equations to the MNA system
        n1, n2 = self.Nodes[0].Index, self.Nodes[1].Index
        # ... stamp logic ...
    
    def UpdateState(self, solution, context):
        # Store internal state for next time-step
        pass
    
    def GetCurrent(self, solution):
        # Return branch current for probing
        return 0.0
```

---

## Roadmap

- [ ] Current sources
- [ ] Controlled sources (VCVS, CCVS, VCCS, CCCS)
- [ ] Non-linear components (diodes, transistors)
- [ ] DC operating point analysis
- [ ] AC frequency sweep (Bode plots)
- [ ] Sparse matrix solver for large circuits
- [ ] Subcircuits and hierarchical design
- [ ] Netlist import/export

---

## Contributing

Contributions are welcome! Please open an issue or pull request on GitHub.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

**Copyright © 2026 Arnav Choudhary**

---

## Acknowledgments

PyEEL's MNA formulation is inspired by:

- **SPICE** (Simulation Program with Integrated Circuit Emphasis)
- *"The SPICE Book"* by Vladimirescu (1994)
- *"Computer Methods for Circuit Analysis and Design"* by Vlach & Singhal (1983)

Backward-Euler integration for reactive components follows standard SPICE companion models.
