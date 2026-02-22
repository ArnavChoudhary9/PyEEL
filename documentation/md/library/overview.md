# Component Library

The **pre-built component library** provides factory functions for
real-world electronic parts with **datasheet parameters already filled in**.
Each function takes only a `name` and `nodes` tuple — no need to look up
$I_S$, $\beta_F$, or $V_Z$ values.

```python
from PyEEL.Components.library import IN4007, BC547, R1k, LED_Red

ckt.AddComponent(R1k("R1", (n1, n2)))
ckt.AddComponent(IN4007("D1", (n_anode, n_cathode)))
ckt.AddComponent(BC547("Q1", (n_c, n_b, n_e)))
ckt.AddComponent(LED_Red("LED1", (n_a, n_k)))
```

## Available Parts

### Power Sources

| Function | Description |
|---|---|
| `DC3V3(name, nodes)` | 3.3 V DC supply |
| `DC5V(name, nodes)` | 5 V DC supply |
| `DC12V(name, nodes)` | 12 V DC supply |
| `DC24V(name, nodes)` | 24 V DC supply |
| `AC240V_50Hz(name, nodes)` | 240 V RMS 50 Hz mains (peak ≈ 339 V) |
| `AC120V_60Hz(name, nodes)` | 120 V RMS 60 Hz mains (peak ≈ 170 V) |

### Standard Resistors

| Function | Value |
|---|---|
| `R10` | 10 Ω |
| `R100` | 100 Ω |
| `R220` | 220 Ω |
| `R330` | 330 Ω |
| `R470` | 470 Ω |
| `R1k` | 1 kΩ |
| `R2k2` | 2.2 kΩ |
| `R4k7` | 4.7 kΩ |
| `R5k` | 5 kΩ |
| `R10k` | 10 kΩ |
| `R22k` | 22 kΩ |
| `R47k` | 47 kΩ |
| `R100k` | 100 kΩ |
| `R1M` | 1 MΩ |

### Standard Capacitors

| Function | Value | Typical Use |
|---|---|---|
| `C100p` | 100 pF | RF, high-frequency |
| `C1n` | 1 nF | Timing |
| `C10n` | 10 nF | Filtering |
| `C100n` | 100 nF | Universal decoupling |
| `C1u` | 1 µF | Coupling, timing |
| `C10u` | 10 µF | Bypass |
| `C100u` | 100 µF | PSU filtering |
| `C470u` | 470 µF | PSU filtering |
| `C1000u` | 1000 µF | PSU bulk filter |

### Rectifier Diodes

| Function | Part | $I_S$ | $n$ | Rating |
|---|---|---|---|---|
| `IN4001` | 1N4001 | `2.55e-9` | `1.75` | 50 V, 1 A |
| `IN4007` | 1N4007 | `7.02e-9` | `1.77` | 1000 V, 1 A |

### Signal Diodes

| Function | Part | $I_S$ | $n$ | Application |
|---|---|---|---|---|
| `IN4148` | 1N4148 | `2.52e-9` | `1.75` | Fast signal, 75 V |
| `IN914` | 1N914 | `2.52e-9` | `1.75` | Same as 1N4148 |

### Schottky Diodes

| Function | Part | $I_S$ | $n$ | $V_f$ |
|---|---|---|---|---|
| `IN5817` | 1N5817 | `3.19e-5` | `1.05` | ≈ 0.32 V |
| `IN5819` | 1N5819 | `2.5e-5` | `1.05` | ≈ 0.34 V |
| `BAT54` | BAT54 | `1.0e-5` | `1.03` | ≈ 0.24 V |

### Zener Diodes

| Function | Alias | $V_Z$ | $I_{BV}$ |
|---|---|---|---|
| `BZX55C3V3` | `Zener3V3` | 3.3 V | 5 mA |
| `BZX55C5V1` | `Zener5V1` | 5.1 V | 5 mA |
| `BZX55C6V2` | `Zener6V2` | 6.2 V | 5 mA |
| `BZX55C12` | `Zener12V` | 12 V | 1 mA |
| `BZX55C15` | `Zener15V` | 15 V | 1 mA |

### LEDs

| Function | Colour | $V_f$ approx | $I_S$ | $n$ |
|---|---|---|---|---|
| `LED_Red` | Red | 1.8 V | `1.2e-20` | `1.8` |
| `LED_Green` | Green | 2.1 V | `1.0e-22` | `1.9` |
| `LED_Blue` | Blue | 3.2 V | `1.0e-30` | `2.1` |
| `LED_Yellow` | Yellow | 2.0 V | `5.0e-22` | `1.85` |
| `LED_White` | White | 3.2 V | `1.0e-30` | `2.1` |

### NPN Transistors

All use `nodes = (collector, base, emitter)`.

| Function | Part | $\beta_F$ | $I_S$ | $V_{AF}$ | Application |
|---|---|---|---|---|---|
| `N2N2222` | 2N2222 | 256 | `14.34e-15` | 74 V | General purpose |
| `BC547` | BC547 | 400 | `1.8e-14` | 80 V | Small signal |
| `BC548` | BC548 | 400 | `1.8e-14` | 80 V | Small signal |
| `BC549` | BC549 | 420 | `1.8e-14` | 80 V | Low noise |
| `N2N3904` | 2N3904 | 416 | `6.73e-15` | 74 V | General purpose |
| `TIP31C` | TIP31C | 50 | `1e-12` | 100 V | Medium power |
| `TIP41C` | TIP41C | 60 | `1e-12` | 100 V | High power |
| `N2N3055` | 2N3055 | 50 | `2e-11` | 100 V | Power (115 W) |
| `BD139` | BD139 | 100 | `1e-13` | 80 V | Audio driver |
| `S8050` | S8050 | 200 | `1e-14` | 50 V | Low-voltage |

### PNP Transistors

| Function | Part | $\beta_F$ | $I_S$ | $V_{AF}$ | Complement |
|---|---|---|---|---|---|
| `N2N3906` | 2N3906 | 181 | `1.3e-14` | 18.7 V | 2N3904 |
| `BC557` | BC557 | 330 | `1.8e-14` | 60 V | BC547 |
| `BC558` | BC558 | 330 | `1.8e-14` | 60 V | BC548 |
| `N2N2907` | 2N2907 | 200 | `6.5e-15` | 115 V | 2N2222 |
| `TIP32C` | TIP32C | 50 | `1e-12` | 100 V | TIP31C |
| `TIP42C` | TIP42C | 60 | `1e-12` | 100 V | TIP41C |
| `BD140` | BD140 | 100 | `1e-13` | 80 V | BD139 |
| `S8550` | S8550 | 200 | `1e-14` | 50 V | S8050 |

### Darlington Transistors

| Function | Part | Type | $\beta_F$ | Application |
|---|---|---|---|---|
| `TIP120` | TIP120 | NPN | 1000 | Switching heavy loads |
| `TIP125` | TIP125 | PNP | 1000 | Complement of TIP120 |
| `N2N5306` | 2N5306 | NPN | 2500 | Small-signal Darlington |

### Transformers (240 V Primary)

| Function | Ratio | $L_1$ | $L_2$ | $k$ |
|---|---|---|---|---|
| `Transformer_240_to_5(name, primary_nodes, secondary_nodes)` | 48:1 | 100 H | 0.0434 H | 0.999 |
| `Transformer_240_to_12(name, primary_nodes, secondary_nodes)` | 20:1 | 100 H | 0.25 H | 0.999 |
| `Transformer_240_to_24(name, primary_nodes, secondary_nodes)` | 10:1 | 100 H | 1.0 H | 0.999 |

> Transformer functions take `(name, primary_nodes, secondary_nodes)` instead
> of `(name, nodes)`.

## Adding Your Own Parts

See [Adding Library Parts](../extending/new-library-parts.md) for how to
extend this library with new components.
