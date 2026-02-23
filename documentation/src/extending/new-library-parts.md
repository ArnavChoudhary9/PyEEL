# Adding Library Parts

The pre-built component library lives in `PyEEL/Components/library/`, a
package split by category:

| Sub-module | Contents |
|---|---|
| `sources.py` | DC & AC voltage sources |
| `resistors.py` | Standard resistor values (E24+) |
| `capacitors.py` | Ceramic, film & electrolytic capacitors |
| `inductors.py` | Inductors from 1 µH to 10 H |
| `diodes.py` | Rectifiers, signal, Schottky, LEDs |
| `zener_diodes.py` | BZX55C series + short aliases |
| `bjt.py` | NPN, PNP & Darlington transistors |
| `mosfets.py` | N-channel & P-channel MOSFETs |
| `transformers.py` | 240 V & 120 V step-down transformers |
| `opamps.py` | General, JFET-input, audio & precision op-amps |
| `comparators.py` | Open-collector & push-pull comparators |

All names are re-exported from the package `__init__.py`, so either of
these imports works:

```python
from PyEEL.Components.library import R1k, IN4007
from PyEEL.Components.library.resistors import R1k
```

## How Library Functions Work

Each library function is an explicitly typed factory that creates a
component with datasheet parameters pre-filled.  The full type signature
is visible to IDEs and type-checkers:

```python
def IN4007(name: str, nodes: tuple[Node, Node]) -> Diode:
    """1N4007 — general-purpose rectifier (1000 V, 1 A)."""
    return Diode(name, nodes, Is=7.02e-9, n=1.77)
```

The pattern:
1. Takes only `name` and `nodes` (no electrical parameters).
2. Returns the appropriate component class with all parameters filled in.
3. Has a docstring with the part name, key specs, and pin order.
4. Full return-type annotation so IDEs auto-complete `.Nodes`, `.Is`, etc.

## Adding a New Diode

```python
def IN5408(name: str, nodes: tuple[Node, Node]) -> Diode:
    """
    1N5408 — power rectifier (1000 V, 3 A).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=4.5e-9, n=1.8)
```

## Adding a New BJT

```python
def BC337(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    BC337 — medium-current NPN (45 V, 800 mA).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.5e-14, BF=350.0, BR=10.0, Nf=1.0, Nr=1.0, Vaf=90.0)
```

## Adding a New Zener Diode

```python
def BZX55C9V1(name: str, nodes: tuple[Node, Node]) -> ZenerDiode:
    """
    BZX55C9V1 — 9.1 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=9.1, Is=1e-14, Ibv=2e-3, n_bv=1.0)
```

## Adding a New MOSFET

```python
def IRF540N(name: str, nodes: tuple[Node, Node, Node]) -> MOSFET:
    """
    IRF540N — N-channel power MOSFET (100 V, 33 A).

    ``nodes = (drain, gate, source)``
    """
    return MOSFET(name, nodes, MOSFETType.NMOS,
                  Kp=20.0, Vth=3.0, lambda_=0.01)
```

## Adding a New Transformer

```python
def Transformer_120_to_12(
    name: str,
    primary_nodes: tuple[Node, Node],
    secondary_nodes: tuple[Node, Node],
) -> Transformer:
    """
    120 V → 12 V step-down transformer (10:1).
    """
    # L_sec = L_pri × (V_out / V_in)²
    return Transformer(name, primary_nodes, secondary_nodes,
                       primary_inductance=100.0,
                       secondary_inductance=1.0,
                       k=0.999)
```

## Where to Find Datasheet Parameters

### For Diodes ($I_S$, $n$)

- Look for SPICE model parameters in the datasheet's "Simulation Model"
  section.
- Alternatively, use two points on the I–V curve to solve:
  
  $$I_S = \frac{I_D}{e^{V_D/(nV_T)} - 1}$$

- Typical $n$ values: 1.0–1.2 (Schottky), 1.5–2.0 (silicon), 1.8–2.1 (LED)

### For BJTs ($I_S$, $\beta_F$, $V_{AF}$)

- $\beta_F$ (hFE): Usually given directly in the datasheet as $h_{FE}$ at
  specified $I_C$ and $V_{CE}$.
- $I_S$: From SPICE model or calculated from $I_C = \beta_F \cdot I_B$.
- $V_{AF}$: From the slope of $I_C$ vs $V_{CE}$ curves, or from the SPICE model.

### For MOSFETs ($K_p$, $V_{th}$, $\lambda$)

- $V_{th}$: Given as $V_{GS(th)}$ in the datasheet.
- $K_p$: Calculated from $I_D$ at a known $V_{GS}$:
  
  $$K_p = \frac{2 I_D}{(V_{GS} - V_{th})^2}$$

- $\lambda$: From the output characteristic slopes.

## Naming Conventions

| Part Type | Naming Convention | Example |
|---|---|---|
| Resistors | `R` + value + SI suffix | `R4k7`, `R100k` |
| Capacitors | `C` + value + SI suffix | `C100n`, `C10u` |
| Diodes | Part number (prefix `IN` for 1N) | `IN4007`, `BAT54` |
| Zener | Manufacturer part number | `BZX55C5V1` |
| LED | `LED_` + colour | `LED_Red` |
| BJT NPN | Part number (prefix `N` for numbers) | `N2N2222`, `BC547` |
| BJT PNP | Same as NPN | `N2N3906`, `BC557` |
| Transformer | `Transformer_` + ratio | `Transformer_240_to_12` |

> Parts starting with a digit get a letter prefix (e.g. `N2N2222` for
> 2N2222) since Python identifiers cannot start with a number.

## Testing Your New Part

```python
from PyEEL import NodeManager
from PyEEL.Components.library import MyNewPart

nm  = NodeManager()
n1  = nm.AddNode("A")
n2  = nm.AddNode("B")
gnd = nm.GroundNode

part = MyNewPart("X1", (n1, n2))
print(f"{part.Name} created successfully")
```

## Adding to the Package

1. Open the appropriate sub-module (e.g. `library/diodes.py` for a new diode).
2. Add your typed factory function at the bottom of the relevant section.
3. Export the name in `library/__init__.py` by adding it to the correct
   `from .submodule import ...` line.

```python
# In library/__init__.py, add to the diodes import:
from .diodes import (
    IN4001, ..., IN5408, MyNewDiode,   # ← add here
)
```
