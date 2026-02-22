# How Simulation Works

PyEEL uses **Modified Nodal Analysis (MNA)** — the same mathematical
framework used by SPICE — to convert a circuit description into a system
of linear equations that can be solved numerically.

## The Simulation Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Build the  │────→│  Finalize &  │────→│   DC OP      │
│   Circuit   │     │  Validate    │     │   Solve      │
└─────────────┘     └──────────────┘     └──────┬───────┘
                                                │
                                    ┌───────────▼───────────┐
                                    │   Transient Loop      │
                                    │                       │
                                    │  1. Build A, b        │
                                    │  2. Stamp components  │
                                    │  3. Solve (linear or  │
                                    │     Newton–Raphson)   │
                                    │  4. Update states     │
                                    │  5. Record probes     │
                                    │  6. Advance clock     │
                                    │                       │
                                    │  Repeat for each dt   │
                                    └───────────────────────┘
```

## Analysis Types

### DC Operating Point

Solves the circuit with all time-derivative terms set to zero:
- Capacitors → open circuits
- Inductors → short circuits (tiny resistance)
- AC sources → their DC value (0 for pure sine)

Uses Newton–Raphson for non-linear circuits, with **source stepping** and
**gmin stepping** as convergence aids.

### Transient Analysis

Advances the simulation one time step at a time using the **Backward Euler**
(or Trapezoidal) integration method.  At each step:

1. Energy-storing elements (C, L) are replaced by their companion models.
2. The MNA system is assembled and solved.
3. Component states are updated for the next step.

## Key Classes

| Class | Role |
|---|---|
| [`Circuit`](../core/circuit.md) | Top-level engine; owns everything |
| `MNASystemBuilder` | Zeros and stamps the A matrix and b vector |
| `NewtonRaphsonSolver` | Iterative solver for non-linear circuits |
| `DCOperatingPointSolver` | Computes the initial DC bias |
| `TopologyValidator` | Checks for common wiring mistakes |
| `AdaptiveTimestep` | Adjusts dt based on solution changes |
| `EnergyChecker` | Warns about unreasonable stored energy |
