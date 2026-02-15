# PyEEL — How the Simulation Works

A mathematical deep-dive into the Modified Nodal Analysis (MNA) engine
that powers PyEEL's transient circuit simulator.

---

## 1  Overview

PyEEL solves linear electrical circuits by assembling them into a single
matrix equation and solving it at every time-step.  The technique used is
called **Modified Nodal Analysis (MNA)**, which is the same formulation
found in industry-standard SPICE simulators.

The simulation loop looks like this:

```plaintext
for each time step  t → t + Δt :
    1.  Assemble  A x = b   (the MNA system)
    2.  Solve for  x
    3.  Extract voltages and currents from  x
```

---

## 2  Nodal Analysis — the Foundation

### 2.1  Kirchhoff's Current Law (KCL)

At every node *k* in the circuit the sum of all currents entering that
node must be zero:

$$
\sum_{j} I_{k \to j} = 0
$$

If we know the relationship between current and voltage for every
component (its *constitutive equation*), we can rewrite each current in
terms of the unknown node voltages and obtain one equation per node.

### 2.2  Ground Reference

One node is designated **ground** (GND) and its voltage is defined as
zero.  This removes one unknown and one equation, keeping the system
square.

---

## 3  Conductance Stamping (Resistors)

For a resistor $R$ connected between nodes $n_1$ and $n_2$, Ohm's law
gives:

$$
I = \frac{V_{n_1} - V_{n_2}}{R} = G \, (V_{n_1} - V_{n_2})
$$

where $G = 1/R$ is the **conductance**.

Writing the KCL contribution at each node:

| Node  | Current contribution         |
|-------|------------------------------|
| $n_1$ | $+G\,V_{n_1} - G\,V_{n_2}$   |
| $n_2$ | $-G\,V_{n_1} + G\,V_{n_2}$   |

This translates directly into a **stamp** — a set of additions to the
global matrix $A$:

$$
A[n_1, n_1] \mathrel{+}= G, \quad
A[n_1, n_2] \mathrel{-}= G
$$
$$
A[n_2, n_1] \mathrel{-}= G, \quad
A[n_2, n_2] \mathrel{+}= G
$$

If either terminal is ground (index `None`), the corresponding
row/column updates are simply omitted because $V_{\text{GND}} = 0$ is
already enforced.

### 3.1  Example — single resistor to ground

Consider $R_1 = 1\,\text{k}\Omega$ between node 0 and GND:

$$
G = \frac{1}{1000} = 0.001\;\text{S}
$$

Only node 0 is a real unknown, so:

$$
A[0, 0] \mathrel{+}= 0.001
$$

---

## 4  Voltage Sources and the "Modified" in MNA

A standard nodal analysis cannot directly handle ideal voltage sources
because they impose a *constraint* rather than a current–voltage
relationship.

MNA solves this by introducing an **auxiliary unknown** $I_s$ — the
branch current through the source — and adding a new equation that
enforces the voltage constraint.

### 4.1  Voltage source stamp

For a source that forces $V_{n_1} - V_{n_2} = v_s$, let $I_s$ be the
unknown current (flowing from $n_1$ to $n_2$ *through* the source).
The auxiliary index is $a$.

**KCL contributions** (current entering the source's terminals):

$$
A[n_1, a] \mathrel{+}= 1, \qquad
A[n_2, a] \mathrel{-}= 1
$$

**KVL constraint** (the extra equation):

$$
A[a, n_1] \mathrel{+}= 1, \qquad
A[a, n_2] \mathrel{-}= 1, \qquad
b[a] = v_s
$$

This makes the system **symmetric** — a desirable property for
numerical solvers.

### 4.2  Full MNA matrix layout

After stamping, the solution vector has the form:

$$
\mathbf{x} =
\begin{bmatrix}
V_0 \\ V_1 \\ \vdots \\ V_{N-1} \\ I_{s,0} \\ I_{s,1} \\ \vdots
\end{bmatrix}
$$

where $N$ is the number of non-ground nodes and the $I_{s,k}$ are the
auxiliary branch currents.

---

## 5  Building the System: $A\mathbf{x} = \mathbf{b}$

At each time-step PyEEL:

1. Allocates an $M \times M$ zero matrix $A$ and an $M$-vector $b$,
   where $M = N + N_{\text{aux}}$.
2. Iterates over every component and calls its `Stamp(A, b, context)`
   method — each component *adds* its contribution (stamps are additive).
3. Solves $A\mathbf{x} = \mathbf{b}$ with a linear solver.

### 5.1  Concrete example — voltage divider

Circuit: $V_s = 5\,\text{V}$ between node 1 and GND, $R_1 = 1\,\text{k}\Omega$
between nodes 1 and 2, $R_2 = 1\,\text{k}\Omega$ between node 2 and
GND.

Nodes: $n_1$ (index 0), $n_2$ (index 1), GND (no index).  
Auxiliary: $I_s$ (index 2).

After stamping:

$$
\underbrace{
\begin{bmatrix}
G_1      & -G_1  & 1 \\
-G_1     & G_1 + G_2 & 0 \\
1        & 0     & 0
\end{bmatrix}
}_{A}
\begin{bmatrix} V_0 \\ V_1 \\ I_s \end{bmatrix}
=
\begin{bmatrix} 0 \\ 0 \\ 5 \end{bmatrix}
$$

where $G_1 = G_2 = 0.001\;\text{S}$.

Solving gives:

$$
V_0 = 5\;\text{V}, \quad V_1 = 2.5\;\text{V}, \quad I_s = -2.5\;\text{mA}
$$

(The negative sign on $I_s$ means the current flows into the positive
terminal of the source — it is *delivering* power, as expected.)

---

## 6  Transient Simulation

For time-domain analysis PyEEL steps through time:

$$
t_k = t_0 + k \cdot \Delta t, \qquad k = 0, 1, 2, \ldots
$$

At each step the source waveforms are evaluated at the current time:

$$
v_s(t_k) = A \sin(2 \pi f \, t_k + \phi)
\qquad\text{(for a sine source)}
$$

Because the resistor stamp is time-invariant, only the right-hand-side
vector $b$ changes between steps (through the waveform value).  The
matrix $A$ is rebuilt from scratch each step to keep the code simple and
correct — an optimisation for large circuits would cache $A$.

### 6.1  Sampling and the Nyquist criterion

When simulating an AC source at frequency $f$, the time-step must
satisfy:

$$
\Delta t \le \frac{1}{2 f}
$$

In practice, 10–20 samples per period give smooth waveforms:

$$
\Delta t \approx \frac{1}{20 f}
$$

---

## 7  Probing

Probes do **not** affect the simulation; they simply observe the
solution vector after each step.

| Probe type           | Formula                                                                |
|----------------------|------------------------------------------------------------------------|
| Single-node voltage  | $V_k = x[k]$                                                           |
| Differential voltage | $V_{k} - V_{j} = x[k] - x[j]$                                          |
| Component current    | Depends on component — resistor: $I = V/R$; voltage source: $I = x[a]$ |

### 7.1  Time-windowed plotting

To keep plots readable the `Probe.Plot(window=W)` method clips the
displayed data to the interval $[t_{\max} - W,\; t_{\max}]$.  This
prevents the x-axis from stretching as the simulation runs and
preserves waveform detail.

---

## 8  Solver Back-end

The default solver (`NumpySolver`) calls `numpy.linalg.solve`, which
performs LU decomposition with partial pivoting:

$$
PA = LU
$$

This has $O(M^3)$ complexity.  For large sparse circuits a sparse solver
(e.g. `scipy.sparse.linalg.spsolve`) would be far more efficient.

---

## 9  Extending PyEEL

To add a new component:

1. Subclass `Component` (or `Source` for excitation elements).
2. Implement `Stamp(A, b, context)` — add your constitutive equations
   to the MNA system.
3. If you need extra unknowns (e.g. branch currents), call
   `NodeManager.RequestAuxiliaryUnknown()` in `RegisterUnknowns`.
4. Implement `GetCurrent` and `GetVoltage` for probing.

### 9.1  Capacitor stamp (future work)

A capacitor $C$ between nodes $n_1$ and $n_2$ in the backward-Euler
discretisation:

$$
I_C = C \frac{V_{n_1}(t) - V_{n_2}(t) - V_{n_1}(t-\Delta t) + V_{n_2}(t-\Delta t)}{\Delta t}
$$

This behaves like a conductance $G_C = C / \Delta t$ plus a history
current source $I_{\text{hist}}$, and is stamped similarly to a resistor
with an additional right-hand-side contribution.

### 9.2  Inductor stamp (future work)

An inductor $L$ in the backward-Euler discretisation adds an auxiliary
current $I_L$ and the equation:

$$
V_{n_1} - V_{n_2} = \frac{L}{\Delta t}(I_L(t) - I_L(t - \Delta t))
$$

---

## 10  Performance Optimizations

PyEEL is designed to run transient simulations in real-time with live
plotting. To achieve ~90,000 simulation steps per second on a typical
machine, several critical optimizations have been implemented.

### 10.1  Batched Simulation Steps

**Problem:** Matplotlib's `plt.pause()` blocks for ~30 ms per call.
Calling `plotter.Update()` after every `Simulate(dt)` step means
simulating 1 second of circuit time at `dt = 0.0005` would take ~60
seconds of wall-clock time.

**Solution:** Batch multiple simulation steps between visual updates:

```python
STEPS_PER_FRAME = 60
while plotter.IsOpen:
    for _ in range(STEPS_PER_FRAME):
        ckt.Simulate(dt)
    plotter.Update()
```

This reduces plot overhead by 60× while maintaining ~30 fps animation.

The `LiveSimulation` class encapsulates this pattern:

```python
sim = LiveSimulation(ckt, plotter, dt=0.0005, speed=60)
sim.Run()
```

### 10.2  Sliced Data Conversion in LivePlotter

**Problem:** Converting the entire probe history from Python lists to
numpy arrays every frame (`np.array(probe.TimeData)`) creates O(N)
growing overhead as the simulation progresses.

**Solution:** When a time window is specified, use `bisect.bisect_left`
to find the start index *before* converting to numpy:

```python
if window is not None and len(probe.TimeData) > 0:
    t_max = probe.TimeData[-1]
    t_min = t_max - window
    idx = bisect.bisect_left(probe.TimeData, t_min)
    t = np.array(probe.TimeData[idx:])    # only convert windowed subset
    v = np.array(probe.ValueData[idx:])
else:
    t = np.array(probe.TimeData)
    v = np.array(probe.ValueData)
```

This eliminates the growing cost for windowed plots.

### 10.3  Pre-allocated MNA System Matrices

**Problem:** Creating new `np.zeros((n, n))` arrays every time-step
incurs allocation overhead in the hottest code path.

**Solution:** Allocate once in `Circuit.Finalize()`, then zero in-place:

```python
def Finalize(self):
    # ... topology freeze ...
    n = self._NodeManager.TotalUnknownCount
    self._A = np.zeros((n, n))
    self._b = np.zeros(n)

def _BuildSystem(self, context):
    self._A[:] = 0.0    # in-place zero — no allocation
    self._b[:] = 0.0
    for component in self._Components:
        component.Stamp(self._A, self._b, context)
    return self._A, self._b
```

For small systems (4×4) this saves ~10% overhead.

### 10.4  Reused SimulationContext

**Problem:** Constructing a new `SimulationContext` dataclass every
time-step involves Python object creation, `__init__` overhead, and
type annotation machinery.

**Solution:** Allocate once, mutate fields each step:

```python
# In Finalize():
self._context = SimulationContext(
    Mode=SimulationMode.TRANSIENT, Time=0.0, dt=0.0
)

# In Simulate():
self._context.Time = self.__T
self._context.dt = dt
self._context.x_prev = self.__x_prev
```

Saves ~5-10% overhead in the main loop.

### 10.5  Direct Attribute Access in Components

**Problem:** Capacitors and inductors used `dict.get()` to retrieve
state variables (`v_prev`, `i_prev`, `current`), incurring dictionary
hashing and lookup overhead every step.

**Solution:** Store state in direct instance attributes:

```python
# In Capacitor.__init__:
self._v_prev = 0.0
self._current = 0.0

# In Stamp():
v_prev = self._v_prev    # ~3× faster than dict.get("v_prev", 0.0)
```

### 10.6  Cached Conductance in Resistors

**Problem:** Resistors recomputed `G = 1.0 / R` on every `Stamp()` call.

**Solution:** Cache in `__init__`:

```python
self._Conductance = 1.0 / resistance
```

### 10.7  Performance Summary

| Optimization                   | Impact on 4×4 circuit | Category          |
|--------------------------------|-----------------------|-------------------|
| Batch simulation steps (60×)   | **~60× speedup**      | Algorithm change  |
| Sliced data conversion         | O(N) → O(window)      | Memory efficiency |
| Pre-allocated matrices         | ~10% faster           | Allocation        |
| Reused SimulationContext       | ~5-10% faster         | Object creation   |
| Direct attributes (not dict)   | ~5% faster            | Micro-optimization|
| Cached conductance             | <1% faster            | Micro-optimization|

Combined, these changes achieve **~90,000 steps/second** for typical
LCR circuits, enabling real-time interactive simulation.

---

## 11  Summary

| Concept               | Mathematical core                              |
|-----------------------|------------------------------------------------|
| Circuit topology      | KCL at every node                              |
| Resistor              | $G = 1/R$ conductance stamp in $A$             |
| Voltage source        | Auxiliary unknown + KVL row in $A$ / $b$       |
| Time stepping         | Re-evaluate $b$ (and $A$ for reactive parts)   |
| Solving               | Dense LU: $A\mathbf{x} = \mathbf{b}$           |
| Probing               | Pure observation of $\mathbf{x}$               |
