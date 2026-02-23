# MNA Formulation

**Modified Nodal Analysis (MNA)** is the mathematical framework at the
heart of PyEEL.  It extends standard nodal analysis to handle voltage
sources and current-measuring elements.

## The MNA Equation

$$
\mathbf{A} \cdot \mathbf{x} = \mathbf{b}
$$

where:

| Symbol | Size | Contents |
|---|---|---|
| $\mathbf{A}$ | $N \times N$ | Conductance matrix (stamps from all components) |
| $\mathbf{x}$ | $N \times 1$ | Unknown vector: node voltages + auxiliary currents |
| $\mathbf{b}$ | $N \times 1$ | Right-hand-side: known currents + voltage constraints |

$N = $ `NodeManager.TotalUnknownCount` = (number of nodes - 1) + (auxiliary unknowns).

## Solution Vector Layout

```
x = [ V_0, V_1, …, V_{n-1},  I_aux0, I_aux1, … ]
     └── node voltages ──┘   └── branch currents ──┘
```

Ground voltage is always 0 and is **not** included in the system.

## Stamping

Each component writes its contribution into `A` and `b` through its
`Stamp(A, b, context)` method.  The `MNASystemBuilder` zeroes both
arrays, then calls every component's stamp in sequence.

### Resistor Stamp

For a resistor $R$ between nodes `i` and `j`, conductance $G = 1/R$:

|   | col `i` | col `j` |
|---|---|---|
| **row `i`** | $+G$ | $-G$ |
| **row `j`** | $-G$ | $+G$ |

### Voltage Source Stamp

A voltage source $V_s$ between nodes `i` and `j` with auxiliary index `k`:

|   | col `i` | col `j` | col `k` |
|---|---|---|---|
| **row `i`** | | | $+1$ |
| **row `j`** | | | $-1$ |
| **row `k`** | $+1$ | $-1$ | |

And $b[k] = V_s$.

### Capacitor Companion Stamp (Backward Euler)

Equivalent conductance $G_{eq} = C/\Delta t$, stamped like a resistor,
plus a history current source $I_h = G_{eq} \cdot V_{prev}$ in `b`.

### Non-Linear Device Stamp

Diodes, BJTs, MOSFETs stamp a **linearised companion model** at each
Newton–Raphson iteration:

- $g_d$ (differential conductance) → into `A`
- $I_{eq}$ (equivalent current source) → into `b`

## Gmin

A small conductance `gmin` (default `1e-12` S) is added from every node
to ground to prevent singular matrices.  This is a standard SPICE technique.

## Building the System

```python
builder = MNASystemBuilder(components, node_manager, gmin=1e-12)
A, b = builder.build(context)
```

The `Circuit` class handles this automatically — you don't call it directly.

## Solving

For **linear** circuits (only resistors, sources, companion models), a
single `numpy.linalg.solve(A, b)` call suffices.

For **non-linear** circuits, the system is solved iteratively by the
[Newton–Raphson solver](newton-raphson.md).
