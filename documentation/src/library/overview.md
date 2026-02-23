# Component Library

The **pre-built component library** (`PyEEL/Components/library/`) provides
165+ explicitly typed factory functions for real-world electronic parts
with **datasheet parameters already filled in**.  Every function has full
return-type annotations so IDEs provide autocomplete and type checking.

```python
from PyEEL.Components.library import IN4007, BC547, R1k, LED_Red

ckt.AddComponent(R1k("R1", (n1, n2)))
ckt.AddComponent(IN4007("D1", (n_anode, n_cathode)))
ckt.AddComponent(BC547("Q1", (n_c, n_b, n_e)))
ckt.AddComponent(LED_Red("LED1", (n_a, n_k)))
```

You can also import from individual sub-modules:

```python
from PyEEL.Components.library.resistors import R1k
from PyEEL.Components.library.mosfets import IRF540N
```

## Available Parts

### Power Sources (`library/sources.py`)

| Function | Description |
|---|---|
| `DC3V3(name, nodes)` | 3.3 V DC supply |
| `DC5V(name, nodes)` | 5 V DC supply |
| `DC9V(name, nodes)` | 9 V DC supply (battery) |
| `DC12V(name, nodes)` | 12 V DC supply |
| `DC15V(name, nodes)` | 15 V DC supply |
| `DC24V(name, nodes)` | 24 V DC industrial supply |
| `DC48V(name, nodes)` | 48 V DC telecom supply |
| `AC240V_50Hz(name, nodes)` | 240 V RMS 50 Hz (AU/UK) |
| `AC230V_50Hz(name, nodes)` | 230 V RMS 50 Hz (EU) |
| `AC120V_60Hz(name, nodes)` | 120 V RMS 60 Hz (US/CA) |
| `AC100V_50Hz(name, nodes)` | 100 V RMS 50 Hz (JP East) |

### Standard Resistors (`library/resistors.py`)

| Function | Value | | Function | Value |
|---|---|---|---|---|
| `R10` | 10 Ω | | `R2k2` | 2.2 kΩ |
| `R22` | 22 Ω | | `R3k3` | 3.3 kΩ |
| `R47` | 47 Ω | | `R4k7` | 4.7 kΩ |
| `R100` | 100 Ω | | `R5k` | 5 kΩ |
| `R150` | 150 Ω | | `R6k8` | 6.8 kΩ |
| `R220` | 220 Ω | | `R10k` | 10 kΩ |
| `R330` | 330 Ω | | `R15k` | 15 kΩ |
| `R470` | 470 Ω | | `R22k` | 22 kΩ |
| `R680` | 680 Ω | | `R33k` | 33 kΩ |
| `R1k` | 1 kΩ | | `R47k` | 47 kΩ |
| `R1k5` | 1.5 kΩ | | `R56k` | 56 kΩ |
| | | | `R68k` | 68 kΩ |
| | | | `R100k` | 100 kΩ |
| | | | `R220k` | 220 kΩ |
| | | | `R470k` | 470 kΩ |
| | | | `R1M` | 1 MΩ |
| | | | `R10M` | 10 MΩ |

### Standard Capacitors (`library/capacitors.py`)

| Function | Value | Typical Use |
|---|---|---|
| `C10p` | 10 pF | RF tuning |
| `C22p` | 22 pF | Crystal load |
| `C47p` | 47 pF | RF |
| `C100p` | 100 pF | RF, high-frequency |
| `C220p` | 220 pF | RF matching |
| `C1n` | 1 nF | Timing |
| `C10n` | 10 nF | Filtering |
| `C22n` | 22 nF | Filtering |
| `C47n` | 47 nF | Filtering |
| `C100n` | 100 nF | Universal decoupling |
| `C1u` | 1 µF | Coupling, timing |
| `C2u2` | 2.2 µF | Coupling |
| `C4u7` | 4.7 µF | Coupling |
| `C10u` | 10 µF | Bypass |
| `C22u` | 22 µF | Bypass |
| `C47u` | 47 µF | Filtering |
| `C100u` | 100 µF | PSU filtering |
| `C220u` | 220 µF | PSU filtering |
| `C470u` | 470 µF | PSU filtering |
| `C1000u` | 1000 µF | PSU bulk filter |
| `C2200u` | 2200 µF | PSU bulk filter |
| `C4700u` | 4700 µF | PSU bulk filter |

### Standard Inductors (`library/inductors.py`)

| Function | Value | Typical Use |
|---|---|---|
| `L1u` | 1 µH | DC-DC converters |
| `L2u2` | 2.2 µH | DC-DC converters |
| `L4u7` | 4.7 µH | DC-DC converters |
| `L10u` | 10 µH | EMI filtering |
| `L22u` | 22 µH | EMI filtering |
| `L47u` | 47 µH | EMI filtering |
| `L100u` | 100 µH | EMI filtering |
| `L220u` | 220 µH | EMI filtering |
| `L470u` | 470 µH | RF choke |
| `L1m` | 1 mH | Audio crossover |
| `L2m2` | 2.2 mH | Audio crossover |
| `L4m7` | 4.7 mH | Audio crossover |
| `L10m` | 10 mH | Audio crossover |
| `L100m` | 100 mH | Power filter |
| `L1H` | 1 H | Power filter |
| `L5H` | 5 H | Filter choke |
| `L10H` | 10 H | Valve amplifier choke |

### Rectifier Diodes (`library/diodes.py`)

| Function | Part | $I_S$ | $n$ | Rating |
|---|---|---|---|---|
| `IN4001` | 1N4001 | `2.55e-9` | `1.75` | 50 V, 1 A |
| `IN4002` | 1N4002 | `2.55e-9` | `1.75` | 100 V, 1 A |
| `IN4004` | 1N4004 | `2.55e-9` | `1.76` | 400 V, 1 A |
| `IN4007` | 1N4007 | `7.02e-9` | `1.77` | 1000 V, 1 A |
| `IN5399` | 1N5399 | `5.0e-9` | `1.78` | 1000 V, 1.5 A |
| `IN5408` | 1N5408 | `4.5e-9` | `1.80` | 1000 V, 3 A |

### Signal Diodes

| Function | Part | $I_S$ | $n$ | Application |
|---|---|---|---|---|
| `IN4148` | 1N4148 | `2.52e-9` | `1.75` | Fast signal, 75 V |
| `IN914` | 1N914 | `2.52e-9` | `1.75` | Same as 1N4148 |
| `IN4454` | 1N4454 | `2.0e-9` | `1.75` | High-speed switching |

### Schottky Diodes

| Function | Part | $I_S$ | $n$ | $V_f$ |
|---|---|---|---|---|
| `IN5817` | 1N5817 | `3.19e-5` | `1.05` | ≈ 0.32 V |
| `IN5819` | 1N5819 | `2.5e-5` | `1.05` | ≈ 0.34 V |
| `IN5822` | 1N5822 | `3.0e-5` | `1.05` | ≈ 0.33 V, 3 A |
| `BAT54` | BAT54 | `1.0e-5` | `1.03` | ≈ 0.24 V |
| `BAT46` | BAT46 | `2.0e-5` | `1.03` | ≈ 0.28 V |

### LEDs

| Function | Colour | $V_f$ approx | $I_S$ | $n$ |
|---|---|---|---|---|
| `LED_Red` | Red | 1.8 V | `1.2e-20` | `1.8` |
| `LED_Orange` | Orange | 2.0 V | `3.0e-21` | `1.85` |
| `LED_Yellow` | Yellow | 2.0 V | `5.0e-22` | `1.85` |
| `LED_Green` | Green | 2.1 V | `1.0e-22` | `1.9` |
| `LED_Blue` | Blue | 3.2 V | `1.0e-30` | `2.1` |
| `LED_White` | White | 3.2 V | `1.0e-30` | `2.1` |
| `LED_IR` | Infrared | 1.2 V | `1.0e-18` | `1.5` |
| `LED_UV` | UV | 3.5 V | `1.0e-32` | `2.2` |

### Zener Diodes (`library/zener_diodes.py`)

| Function | Alias | $V_Z$ | $I_{BV}$ |
|---|---|---|---|
| `BZX55C2V7` | `Zener2V7` | 2.7 V | 10 mA |
| `BZX55C3V3` | `Zener3V3` | 3.3 V | 5 mA |
| `BZX55C3V9` | `Zener3V9` | 3.9 V | 5 mA |
| `BZX55C4V7` | `Zener4V7` | 4.7 V | 5 mA |
| `BZX55C5V1` | `Zener5V1` | 5.1 V | 5 mA |
| `BZX55C5V6` | `Zener5V6` | 5.6 V | 5 mA |
| `BZX55C6V2` | `Zener6V2` | 6.2 V | 5 mA |
| `BZX55C6V8` | `Zener6V8` | 6.8 V | 5 mA |
| `BZX55C7V5` | `Zener7V5` | 7.5 V | 5 mA |
| `BZX55C9V1` | `Zener9V1` | 9.1 V | 2 mA |
| `BZX55C10` | `Zener10V` | 10 V | 2 mA |
| `BZX55C12` | `Zener12V` | 12 V | 1 mA |
| `BZX55C15` | `Zener15V` | 15 V | 1 mA |
| `BZX55C18` | `Zener18V` | 18 V | 1 mA |
| `BZX55C24` | `Zener24V` | 24 V | 0.5 mA |
| `BZX55C33` | `Zener33V` | 33 V | 0.5 mA |

### NPN Transistors (`library/bjt.py`)

All use `nodes = (collector, base, emitter)`.

| Function | Part | $\beta_F$ | $I_S$ | $V_{AF}$ | Application |
|---|---|---|---|---|---|
| `N2N2222` | 2N2222 | 256 | `14.34e-15` | 74 V | General purpose |
| `N2N2222A` | 2N2222A | 300 | `14.34e-15` | 74 V | Improved 2N2222 |
| `BC547` | BC547 | 400 | `1.8e-14` | 80 V | Small signal |
| `BC547B` | BC547B | 450 | `1.8e-14` | 80 V | Higher-gain grade |
| `BC548` | BC548 | 400 | `1.8e-14` | 80 V | Small signal |
| `BC549` | BC549 | 420 | `1.8e-14` | 80 V | Low noise |
| `BC337` | BC337 | 350 | `1.5e-14` | 90 V | Medium current |
| `N2N3904` | 2N3904 | 416 | `6.73e-15` | 74 V | General purpose |
| `MPSA42` | MPSA42 | 60 | `5e-15` | 150 V | High voltage (300 V) |
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
| `MPSA92` | MPSA92 | 60 | `5e-15` | 150 V | MPSA42 |
| `TIP32C` | TIP32C | 50 | `1e-12` | 100 V | TIP31C |
| `TIP42C` | TIP42C | 60 | `1e-12` | 100 V | TIP41C |
| `BD140` | BD140 | 100 | `1e-13` | 80 V | BD139 |
| `S8550` | S8550 | 200 | `1e-14` | 50 V | S8050 |
| `BC560` | BC560 | 420 | `1.8e-14` | 60 V | Low-noise PNP |

### Darlington Transistors

| Function | Part | Type | $\beta_F$ | Application |
|---|---|---|---|---|
| `TIP120` | TIP120 | NPN | 1000 | Switching heavy loads |
| `TIP121` | TIP121 | NPN | 1000 | 80 V version |
| `TIP122` | TIP122 | NPN | 1000 | 100 V version |
| `TIP125` | TIP125 | PNP | 1000 | Complement of TIP120 |
| `TIP126` | TIP126 | PNP | 1000 | Complement of TIP121 |
| `TIP127` | TIP127 | PNP | 1000 | Complement of TIP122 |
| `N2N5306` | 2N5306 | NPN | 2500 | Small-signal Darlington |

### N-Channel MOSFETs (`library/mosfets.py`)

All use `nodes = (drain, gate, source)`.

| Function | Part | $K_p$ | $V_{th}$ | $\lambda$ | Application |
|---|---|---|---|---|---|
| `IRF540N` | IRF540N | 20.0 | 3.0 V | 0.01 | Power MOSFET (100 V, 33 A) |
| `IRF530N` | IRF530N | 10.0 | 3.0 V | 0.01 | Power (100 V, 17 A) |
| `IRF9540N` | IRF9540N | 8.0 | −3.5 V | 0.01 | P-ch power (note: NMOS model) |
| `IRF3205` | IRF3205 | 40.0 | 2.0 V | 0.005 | Low $R_{DS}$ (55 V, 110 A) |
| `IRFZ44N` | IRFZ44N | 25.0 | 3.0 V | 0.008 | Logic-level (55 V, 49 A) |
| `N2N7000` | 2N7000 | 0.1 | 2.0 V | 0.04 | Small-signal (60 V, 200 mA) |
| `BS170` | BS170 | 0.15 | 2.0 V | 0.04 | Small-signal |
| `IRF840` | IRF840 | 3.0 | 4.0 V | 0.007 | High-voltage (500 V, 8 A) |
| `IRLZ44N` | IRLZ44N | 30.0 | 1.5 V | 0.008 | Logic-level gate |
| `STP55NF06` | STP55NF06 | 35.0 | 2.5 V | 0.006 | Low $R_{DS}$ (60 V, 50 A) |

### P-Channel MOSFETs

| Function | Part | $K_p$ | $V_{th}$ | $\lambda$ | Application |
|---|---|---|---|---|---|
| `IRF9540` | IRF9540 | 8.0 | −3.5 V | 0.01 | P-ch power (100 V, 23 A) |
| `IRF5305` | IRF5305 | 10.0 | −3.0 V | 0.008 | P-ch power (55 V, 31 A) |
| `TP0610T` | TP0610T | 0.05 | −1.5 V | 0.05 | Small-signal P-ch |
| `VP2106` | VP2106 | 0.03 | −2.0 V | 0.05 | Small-signal P-ch |
| `NDP6020P` | NDP6020P | 5.0 | −2.0 V | 0.01 | Logic-level P-ch (20 V, 24 A) |

### Transformers (`library/transformers.py`)

#### 240 V Primary

| Function | Ratio | $L_1$ | $L_2$ | $k$ |
|---|---|---|---|---|
| `Transformer_240_to_5` | 48:1 | 100 H | 0.0434 H | 0.999 |
| `Transformer_240_to_9` | 26.7:1 | 100 H | 0.1406 H | 0.999 |
| `Transformer_240_to_12` | 20:1 | 100 H | 0.25 H | 0.999 |
| `Transformer_240_to_24` | 10:1 | 100 H | 1.0 H | 0.999 |
| `Transformer_240_to_48` | 5:1 | 100 H | 4.0 H | 0.999 |

#### 120 V Primary

| Function | Ratio | $L_1$ | $L_2$ | $k$ |
|---|---|---|---|---|
| `Transformer_120_to_5` | 24:1 | 25 H | 0.0434 H | 0.999 |
| `Transformer_120_to_12` | 10:1 | 25 H | 0.25 H | 0.999 |
| `Transformer_120_to_24` | 5:1 | 25 H | 1.0 H | 0.999 |

> Transformer functions take `(name, primary_nodes, secondary_nodes)` instead
> of `(name, nodes)`.

### Operational Amplifiers (`library/opamps.py`)

| Function | Part | $A_{OL}$ | $R_{in}$ | $R_{out}$ | Description |
|---|---|---|---|---|---|
| `LM741` | LM741 | 200k | 2 MΩ | 75 Ω | Classic general-purpose |
| `UA741` | µA741 | 200k | 2 MΩ | 75 Ω | Industry-standard clone |
| `LM358` | LM358 | 100k | 2 MΩ | 150 Ω | Dual, single-supply |
| `LM324` | LM324 | 100k | 2 MΩ | 150 Ω | Quad, single-supply |
| `TL071` | TL071 | 200k | 1 TΩ | 100 Ω | Single low-noise JFET |
| `TL072` | TL072 | 200k | 1 TΩ | 100 Ω | Dual low-noise JFET |
| `TL074` | TL074 | 200k | 1 TΩ | 100 Ω | Quad JFET |
| `TL082` | TL082 | 200k | 1 TΩ | 100 Ω | General JFET input |
| `TL084` | TL084 | 200k | 1 TΩ | 100 Ω | Quad JFET |
| `NE5532` | NE5532 | 100k | 300 kΩ | 0.3 Ω | Low-noise audio |
| `NE5534` | NE5534 | 100k | 100 kΩ | 0.3 Ω | Single low-noise audio |
| `OPA2134` | OPA2134 | 1M | 10 TΩ | 1 Ω | Hi-fi audio FET |
| `OPA2604` | OPA2604 | 1M | 10 TΩ | 1 Ω | Dual FET, low distortion |
| `OP07` | OP07 | 500k | 33 MΩ | 60 Ω | Precision, low offset |
| `OP27` | OP27 | 1.5M | 6 MΩ | 70 Ω | Precision low-noise |
| `AD620` | AD620 | 1M | 10 GΩ | 1 Ω | Instrumentation amp |
| `INA128` | INA128 | 1M | 10 GΩ | 1 Ω | Instrumentation amp |
| `IdealOpAmp` | — | 10⁹ | 1 TΩ | 0.001 Ω | Textbook ideal |

> Op-amp functions take `(name, nodes)` where
> `nodes = (non_inv_input, inv_input, output)`.

### Comparators (`library/comparators.py`)

| Function | Part | $R_{in}$ | $R_{out}$ | Description |
|---|---|---|---|---|
| `LM393` | LM393 | 1 MΩ | 50 Ω | Dual, general purpose |
| `LM2903` | LM2903 | 1 MΩ | 50 Ω | Automotive grade |
| `LM339` | LM339 | 1 MΩ | 50 Ω | Quad, single supply |
| `LM311` | LM311 | 500 kΩ | 50 Ω | Fast, with output transistor |
| `TLV3201` | TLV3201 | 100 MΩ | 25 Ω | Rail-to-rail CMOS |
| `TLV3501` | TLV3501 | 100 MΩ | 25 Ω | 4.5 ns propagation |
| `MAX9021` | MAX9021 | 1 TΩ | 10 Ω | Ultra-low power |
| `MAX9042` | MAX9042 | 1 TΩ | 10 Ω | Dual, 2.5 V compatible |
| `IdealComparator` | — | 1 TΩ | 0.001 Ω | Textbook ideal |

> Comparator functions take `(name, nodes, *, V_high=5.0, V_low=0.0)`
> where `nodes = (non_inv_input, inv_input, output)`.

## Adding Your Own Parts

See [Adding Library Parts](../extending/new-library-parts.md) for how to
extend this library with new components.
