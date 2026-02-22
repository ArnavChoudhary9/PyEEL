# Adding Library Parts

The pre-built component library at `PyEEL/Components/library.py` is
designed to be easily extended with new real-world parts.

## How Library Functions Work

Each library function is a thin wrapper that creates a component with
datasheet parameters pre-filled:

```python
def IN4007(name: str, nodes: tuple[Node, Node]) -> Diode:
    """1N4007 — general-purpose rectifier (1000 V, 1 A)."""
    return Diode(name, nodes, Is=7.02e-9, n=1.77)
```

The pattern:
1. Takes only `name` and `nodes` (no electrical parameters).
2. Returns the appropriate component class with all parameters filled in.
3. Has a docstring with the part name, key specs, and pin order.

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
