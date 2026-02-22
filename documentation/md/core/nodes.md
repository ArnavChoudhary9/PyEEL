# Nodes & Node Manager

Nodes are the fundamental building blocks of any circuit.  Every component
connects between two or more nodes, and the simulator solves for the
**voltage at each node** relative to ground.

## `Node`

```python
from PyEEL import Node
```

A `Node` represents a single electrical net.

| Property | Type | Description |
|---|---|---|
| `Name` | `str` | Human-readable label (e.g. `"n1"`, `"Vcc"`) |
| `Index` | `int \| None` | Row/column in the MNA matrix. `None` for ground. |
| `IsGround` | `bool` | `True` when this is the reference node |

You almost never create `Node` objects directly — use the **NodeManager**
instead.

## `NodeManager`

```python
nm = ckt.NodeManager          # get from a Circuit instance
gnd = nm.GroundNode           # reference node (0 V, always exists)
```

The `NodeManager` is the factory for all nodes in a circuit.

### Creating Nodes

```python
n1  = nm.AddNode("n1")
n2  = nm.AddNode("Vcc")
n3  = nm.AddNode("output")
```

`AddNode` assigns a sequential integer index to each node, which becomes
its row/column position in the MNA system.

> **Tip:** Node names must be unique.  Trying to add a duplicate raises
> `ValueError`.

### Looking Up Nodes

```python
node = nm.GetNode("n1")                            # returns Node or None
node = nm.GetNode("n1", create_if_missing=True)     # creates if absent
```

### Freezing

After `Circuit.Finalize()`, the node manager is **frozen** — no new nodes
can be added.  This is required before auxiliary unknowns (e.g. voltage-source
branch currents) are allocated.

### Properties

| Property | Description |
|---|---|
| `GroundNode` | The GND reference node |
| `VoltageUnknownCount` | Number of non-ground nodes |
| `AuxiliaryUnknownCount` | Extra unknowns (branch currents) |
| `TotalUnknownCount` | Size of the MNA solution vector |
| `NodesFrozen` | `True` after `Freeze()` |

### Solution Vector Layout

The MNA solution vector is laid out as:

```
[ V_node0, V_node1, …, V_nodeN-1, I_aux0, I_aux1, … ]
  ←── voltage unknowns ──→  ←── auxiliary unknowns ──→
```

Ground is excluded (its voltage is defined as 0).
