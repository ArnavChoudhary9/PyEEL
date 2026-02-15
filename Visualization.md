# PyEEL — Circuit Visualization Pipeline

Technical documentation for the graph-based schematic drawing system.

---

## 1  Overview

PyEEL converts a circuit into a visual schematic through a three-stage
pipeline:

```text
Circuit         →    CircuitGraph         →    SchematicsDrawer
(components,         (NetworkX MultiGraph,      (schemdraw rendering,
 nodes, MNA)          structural analysis)       positioned elements)
```

| Stage | Module | Input | Output |
| ------- | -------- | ------- | -------- |
| 1. Graph extraction | `CircuitGraph` | `Circuit` object | `networkx.MultiGraph` |
| 2. Layout (planned) | `SchematicsDrawer` | `CircuitGraph` | 2D node positions |
| 3. Rendering (planned) | `SchematicsDrawer` | positions + metadata | schemdraw figure |

---

## 2  Stage 1 — Graph Extraction (`CircuitGraph`)

Status: Complete

### 2.1  Data Model

The circuit is represented as a `networkx.MultiGraph`:

- **Nodes** = circuit nodes (including GND)
  - Attributes: `node`, `is_ground`, `label`
- **Edges** = components connecting two nodes
  - Key: component name (e.g. `"R1"`)
  - Attributes: `component`, `name`, `type`, `value`
  - Sources also carry: `waveform`, `frequency`, `amplitude`

A `MultiGraph` is used (not `Graph`) because two nodes can be connected
by multiple components in parallel.

### 2.2  Structural Analysis

`CircuitGraph` provides methods to analyze circuit topology before
layout:

| Method | Purpose |
| -------- | --------- |
| `FindSeriesChains()` | Walk degree-2 nodes to find maximal series paths |
| `FindParallelComponents()` | Find node pairs with multiple edges |
| `IsSeriesPath(*nodes)` | Check if intermediate nodes are all degree-2 |
| `Degree(node)` | Connection count (junction detection) |
| `ComponentsByType(type)` | Filter edges by component type |
| `Neighbors(node)` | Adjacent nodes |

### 2.3  Series Chain Detection Algorithm

```text
junctions = { n ∈ V : degree(n) ≠ 2 }

for each junction j:
    for each neighbor n of j:
        walk from j through n along degree-2 nodes
        until reaching another junction
        → this path is one series chain
```

**Output** for the LCR demo circuit:

```text
GND → n1 → n2 → n3 → GND  (V1, L1, C1, R1)
```

Since all nodes have degree 2 (single loop), GND is the only junction
and the entire circuit is one series chain.

### 2.4  Parallel Detection Algorithm

```text
for each unique node pair (u, v):
    if number_of_edges(u, v) > 1:
        → parallel group
```

---

## 3  Stage 2 — Layout Algorithm (Planned)

### 3.1  Design Goals

- Produce clean, readable schematics for common topologies
- Handle both simple (series loops) and complex (bridge, ladder) circuits
- Place components on an orthogonal grid (horizontal / vertical only)
- Minimize wire crossings

### 3.2  Approach: Pattern Recognition + Graph Layout

The layout engine will use a two-pass strategy:

**Pass 1 — Pattern matching** (topology-specific rules):

| Pattern | Detection | Layout rule |
| --------- | ----------- | ------------- |
| Series loop | Single chain from GND back to GND | Rectangle: source on left (vertical), series components across top, return wire along bottom |
| Voltage divider | Source + two series resistors to GND | Source on left, R1 top, R2 bottom, output tap at midpoint |
| Wheatstone bridge | 4 resistors + source forming a diamond | Diamond layout with galvanometer across midpoints |
| LC / RC / RL filter | Source + reactive element + resistor, output tap | L-shape with input on left, output on right |
| Ladder network | Alternating series/shunt elements | Horizontal ladder |

**Pass 2 — Generic fallback** (graph-based):

For circuits that don't match any known pattern:

1. Use NetworkX `spring_layout` or `planar_layout` to get initial positions
2. Snap positions to an orthogonal grid
3. Route wires to avoid crossings

### 3.3  Coordinate System

```text
        (0, H)                    (W, H)
          ┌─────── top rail ─────────┐
          │                          │
  source  │    components →          │  return
  (left)  │                          │  wire
          │                          │
          └─────── bottom rail ──────┘
        (0, 0)                    (W, 0)
                    GND
```

- Components placed along horizontal/vertical rails
- Each component occupies one grid unit (3.0 schemdraw units)
- Wires fill gaps between component endpoints and node positions
- Ground symbols placed at bottom

---

## 4  Stage 3 — Rendering with schemdraw (Planned)

### 4.1  Component Mapping

| PyEEL type | schemdraw element |
| ------------ | ------------------- |
| `Resistor` | `elm.Resistor` |
| `Capacitor` | `elm.Capacitor` |
| `Inductor` | `elm.Inductor` |
| `VoltageSource` (DC) | `elm.SourceV` |
| `VoltageSource` (AC) | `elm.SourceSin` |
| Ground node | `elm.Ground` |
| Wire | `elm.Line` |
| Junction (degree > 2) | `elm.Dot` |

### 4.2  Label Format

Each component is labeled with its name and SI-prefixed value:

```text
R1          V1
1 kΩ        5 V, 60 Hz
```

### 4.3  Rendering API (Planned)

```python
drawer = SchematicsDrawer(circuit_graph)
drawer.Draw()           # show the schematic
drawer.Save("out.png")  # save to file
drawer.Save("out.svg")  # vector output
```

---

## 5  Component Value Formatting

Values are displayed with SI prefixes for readability:

| Threshold | Prefix | Example |
| ----------- | -------- | --------- |
| ≥ 1e12 | T | 1 TΩ |
| ≥ 1e9 | G | 2.2 GΩ |
| ≥ 1e6 | M | 10 MΩ |
| ≥ 1e3 | k | 4.7 kΩ |
| ≥ 1 | (none) | 100 Ω |
| ≥ 1e-3 | m | 100 mH |
| ≥ 1e-6 | μ | 10 μF |
| ≥ 1e-9 | n | 47 nF |
| ≥ 1e-12 | p | 22 pF |

Unit suffixes: Ω (resistor), F (capacitor), H (inductor), V (source).

---

## 6  Dependencies

| Library | Purpose | Version |
| --------- | --------- | --------- |
| `networkx` | Graph representation and algorithms | ≥ 3.0 |
| `schemdraw` | Schematic rendering | ≥ 0.18 |
| `matplotlib` | Backend for schemdraw | ≥ 3.5 |

---

## 7  Progress Tracker

- [x] `CircuitGraph` — graph extraction from `Circuit`
- [x] Structural analysis (series chains, parallel groups, degree)
- [x] SI-prefixed value formatting
- [ ] Pattern recognition (series loop, divider, bridge, filter)
- [ ] Layout algorithm (pattern-specific + generic fallback)
- [ ] `SchematicsDrawer` — schemdraw rendering
- [ ] Node labels and junction dots
- [ ] Wire routing (orthogonal, crossing-free)
- [ ] `Save()` / `Draw()` API
- [ ] Complex topology tests (bridge, ladder, multi-loop)
