# Transient Analysis

Transient analysis simulates the circuit's behaviour over time by advancing
the solution in discrete time steps using numerical integration.

## Integration Methods

### Backward Euler (Default)

$$
\frac{dx}{dt} \approx \frac{x_n - x_{n-1}}{\Delta t}
$$

- **First-order** accurate ($O(\Delta t)$)
- **Unconditionally stable** — will not oscillate regardless of time step
- Introduces numerical **damping** (high-frequency transients decay faster)
- Best choice for circuits with switching, power electronics, start-up

### Trapezoidal

$$
\frac{dx}{dt} \approx \frac{2(x_n - x_{n-1})}{\Delta t} - \left.\frac{dx}{dt}\right|_{n-1}
$$

- **Second-order** accurate ($O(\Delta t^2)$)
- Less numerical damping — better for oscillatory circuits (LCR)
- Can introduce **ringing** on stiff circuits (power supplies, switching)

### Choosing a Method

| Circuit Type | Recommended Method |
|---|---|
| Power supplies, rectifiers | Backward Euler |
| Oscillators, LCR resonance | Trapezoidal |
| General purpose | Backward Euler |

```python
config = SimulationConfig(integration_method=IntegrationMethod.TRAPEZOIDAL)
```

## Companion Models

During transient analysis, energy-storage elements are replaced by
**companion models** — equivalent circuits made of resistors and current
sources:

### Capacitor (Backward Euler)

$$
G_{eq} = \frac{C}{\Delta t}, \qquad I_{hist} = G_{eq} \cdot V_{n-1}
$$

Stamps as a conductance $G_{eq}$ in parallel with a current source $I_{hist}$.

### Inductor (Backward Euler)

$$
G_{eq} = \frac{\Delta t}{L}, \qquad I_{hist} = I_{n-1}
$$

The inductor's auxiliary current unknown carries the history.

## Choosing the Time Step

The time step `dt` determines accuracy and speed:

| Guideline | Rule of Thumb |
|---|---|
| **Nyquist** | $\Delta t < \frac{1}{10 f_{max}}$ for accurate waveforms |
| **Power-line circuits** (50/60 Hz) | $\Delta t = 10^{-4}$ to $10^{-5}$ s |
| **Audio circuits** (20 kHz) | $\Delta t = 10^{-6}$ s |
| **RF circuits** (MHz) | $\Delta t = 10^{-8}$ to $10^{-9}$ s |

Too large → inaccurate waveforms.  Too small → simulation runs slowly.

## Adaptive Time-Step

Enable automatic step-size control:

```python
config = SimulationConfig(
    adaptive_timestep=True,
    adaptive_threshold=0.5,    # normalised change threshold
    adaptive_shrink=0.5,       # shrink factor on rejection
    adaptive_grow=1.05,        # grow factor on acceptance
    max_grow_factor=2.0,       # max single-step growth
)
```

The adaptive controller compares the solution change between steps; if
the change exceeds `adaptive_threshold`, the step is shrunk.  Otherwise
it gradually grows.

## Running Transient Analysis

### Option 1 — LiveSimulation (interactive)

```python
plotter = LivePlotter([voltage_probe, current_probe])
sim     = LiveSimulation(ckt, plotter, dt=1e-4, speed=100)
sim.Run()    # blocks until window is closed
```

### Option 2 — Manual Loop (headless)

```python
for _ in range(100_000):
    ckt.Simulate(dt=1e-4)

# Access probe data
times  = voltage_probe.TimeData
values = voltage_probe.ValueData
```
