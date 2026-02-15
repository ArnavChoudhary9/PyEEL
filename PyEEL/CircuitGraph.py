"""
CircuitGraph — NetworkX-based graph representation of a PyEEL circuit.

Converts the component/node topology into a ``networkx.MultiGraph``
that can be analyzed for structural patterns, laid out with graph
algorithms, and ultimately rendered to a schematic.

Usage
-----
::

    from PyEEL.CircuitGraph import CircuitGraph

    graph = CircuitGraph(ckt)
    graph.Summary()          # print nodes, edges, and component info
    G = graph.Graph          # access the raw NetworkX MultiGraph

Each graph **node** corresponds to a circuit :class:`Node` (including
GND).  Each graph **edge** corresponds to a :class:`Component`, carrying
metadata such as component type, name, and value.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx

if TYPE_CHECKING:
    from .Circuit import Circuit

from .Node import Node
from .Components.Component import Component
from .Components.Resistor import Resistor
from .Components.Capacitor import Capacitor
from .Components.Inductor import Inductor
from .Components.Sources.VoltageSource import VoltageSource
from .Components.Sources.Waveform import SineWave, ConstantWave


# ── helpers ─────────────────────────────────────────────────────────
def _component_type(comp: Component) -> str:
    """Return a short string tag for the component class."""
    if isinstance(comp, Resistor):
        return "R"
    if isinstance(comp, Capacitor):
        return "C"
    if isinstance(comp, Inductor):
        return "L"
    if isinstance(comp, VoltageSource):
        return "V"
    return type(comp).__name__


def _component_value(comp: Component) -> float | None:
    """Extract the primary numeric value of a component."""
    if isinstance(comp, Resistor):
        return comp.Resistance
    if isinstance(comp, Capacitor):
        return comp.Capacitance
    if isinstance(comp, Inductor):
        return comp.Inductance
    if isinstance(comp, VoltageSource):
        wf = comp._Waveform
        return wf.StaticValue
    return None


def _component_info(comp: Component) -> dict:
    """Build a metadata dict for a graph edge."""
    info: dict = {
        "component": comp,
        "name": comp.Name,
        "type": _component_type(comp),
        "value": _component_value(comp),
    }

    # Extra detail for sources
    if isinstance(comp, VoltageSource):
        wf = comp._Waveform
        if isinstance(wf, SineWave):
            info["waveform"] = "AC"
            info["frequency"] = wf._Frequency
            info["amplitude"] = wf._Amplitude
        elif isinstance(wf, ConstantWave):
            info["waveform"] = "DC"
        else:
            info["waveform"] = type(wf).__name__

    return info


def _format_value(value: float | None, comp_type: str) -> str:
    """Human-readable SI-prefixed value string."""
    if value is None:
        return ""

    si = [
        (1e12, "T"), (1e9, "G"), (1e6, "M"), (1e3, "k"),
        (1, ""), (1e-3, "m"), (1e-6, "μ"), (1e-9, "n"), (1e-12, "p"),
    ]
    unit = {"R": "Ω", "C": "F", "L": "H", "V": "V"}.get(comp_type, "")

    abs_val = abs(value)
    for threshold, prefix in si:
        if abs_val >= threshold:
            scaled = value / threshold
            # Clean trailing zeros
            if scaled == int(scaled):
                return f"{int(scaled)} {prefix}{unit}"
            return f"{scaled:.2g} {prefix}{unit}"

    return f"{value:.2g} {unit}"


# ════════════════════════════════════════════════════════════════════
class CircuitGraph:
    """
    Graph representation of a PyEEL :class:`Circuit`.

    Parameters
    ----------
    circuit : Circuit
        The circuit to convert.  Components and nodes are read
        directly; the circuit does **not** need to be finalized.

    Attributes
    ----------
    Graph : nx.MultiGraph
        The underlying NetworkX multigraph.  Nodes carry ``is_ground``
        and ``label`` attributes.  Edges carry component metadata
        (``name``, ``type``, ``value``, ``component``).
    """

    _graph: nx.MultiGraph
    _components: list[Component]
    _node_names: dict[str, Node]

    def __init__(self, circuit: "Circuit"):
        self._graph = nx.MultiGraph()
        self._components = list(circuit._Components)
        self._node_names = {}
        self._build(circuit)

    # ── construction ────────────────────────────────────────────────
    def _build(self, circuit: "Circuit") -> None:
        """Populate the graph from the circuit's nodes and components."""
        nm = circuit.NodeManager

        # Add all registered nodes (including GND)
        for name, node in nm._Nodes.items():
            self._graph.add_node(
                name,
                node=node,
                is_ground=node.IsGround,
                label=name,
            )
            self._node_names[name] = node

        # Add each component as an edge between its two terminal nodes
        for comp in self._components:
            n1_name = comp.Nodes[0].Name
            n2_name = comp.Nodes[1].Name
            info = _component_info(comp)
            self._graph.add_edge(n1_name, n2_name, key=comp.Name, **info)

    # ── properties ──────────────────────────────────────────────────
    @property
    def Graph(self) -> nx.MultiGraph:
        """The raw NetworkX multigraph."""
        return self._graph

    @property
    def Nodes(self) -> list[str]:
        """List of node names."""
        return list(self._graph.nodes)

    @property
    def Components(self) -> list[Component]:
        """All components in the graph."""
        return self._components

    @property
    def GroundNode(self) -> str:
        """Name of the ground node."""
        for name, data in self._graph.nodes(data=True):
            if data.get("is_ground"):
                return name
        raise RuntimeError("No ground node found in graph.")

    # ── queries ─────────────────────────────────────────────────────
    def Neighbors(self, node_name: str) -> list[str]:
        """Return node names adjacent to *node_name*."""
        return list(self._graph.neighbors(node_name))

    def ComponentsBetween(self, n1: str, n2: str) -> list[dict]:
        """Return metadata dicts for all components between two nodes."""
        if not self._graph.has_edge(n1, n2):
            return []
        return [data for _, data in self._graph[n1][n2].items()]

    def ComponentsByType(self, comp_type: str) -> list[dict]:
        """Return all edge-data dicts matching *comp_type* ('R', 'C', etc.)."""
        results = []
        for u, v, data in self._graph.edges(data=True):
            if data.get("type") == comp_type:
                results.append({"from": u, "to": v, **data})
        return results

    def Degree(self, node_name: str) -> int:
        """Number of component connections at a node."""
        return int(dict(self._graph.degree([node_name]))[node_name])  # type: ignore[operator]

    def IsSeriesPath(self, *node_names: str) -> bool:
        """
        Check whether the given nodes form a simple series chain
        (each intermediate node has degree 2).
        """
        deg = dict(self._graph.degree(node_names[1:-1]))  # type: ignore[operator]
        return all(d == 2 for d in deg.values())

    def FindSeriesChains(self) -> list[list[str]]:
        """
        Identify maximal series chains — paths through degree-2 nodes.

        Returns a list of node-name lists.  Each list starts and ends
        at a node with degree != 2 (a junction or terminal).
        """
        visited_edges: set[tuple] = set()
        chains: list[list[str]] = []

        # Junctions / terminals = nodes with degree != 2
        deg_map = dict(self._graph.degree())  # type: ignore[operator]
        junctions = {n for n, d in deg_map.items() if d != 2}

        for junc in junctions:
            for neighbor in self._graph.neighbors(junc):
                edge_key = (min(junc, neighbor), max(junc, neighbor))
                if edge_key in visited_edges:
                    continue

                # Walk along degree-2 nodes
                chain = [junc]
                prev, curr = junc, neighbor
                while curr not in junctions:
                    chain.append(curr)
                    visited_edges.add(
                        (min(prev, curr), max(prev, curr))
                    )
                    # Move to next neighbor that isn't prev
                    nbrs = [n for n in self._graph.neighbors(curr)
                            if n != prev]
                    if not nbrs:
                        break
                    prev, curr = curr, nbrs[0]

                chain.append(curr)
                visited_edges.add(
                    (min(prev, curr), max(prev, curr))
                )
                chains.append(chain)

        return chains

    def FindParallelComponents(self) -> list[tuple[str, str, list[dict]]]:
        """
        Find node pairs connected by more than one component (parallel).

        Returns list of ``(node_a, node_b, [edge_data, ...])``.
        """
        parallels = []
        seen: set[tuple] = set()
        for u, v, _ in self._graph.edges:
            pair = (min(u, v), max(u, v))
            if pair in seen:
                continue
            seen.add(pair)
            edges = self.ComponentsBetween(u, v)
            if len(edges) > 1:
                parallels.append((u, v, edges))
        return parallels

    # ── output ──────────────────────────────────────────────────────
    def Summary(self) -> None:
        """Print a human-readable summary of the circuit graph."""
        print(f"CircuitGraph: {self._graph.number_of_nodes()} nodes, "
              f"{self._graph.number_of_edges()} components")
        print()

        print("Nodes:")
        deg_map = dict(self._graph.degree())  # type: ignore[operator]
        for name, data in self._graph.nodes(data=True):
            deg = deg_map[name]
            gnd = " (GND)" if data.get("is_ground") else ""
            print(f"  {name}{gnd}  degree={deg}")
        print()

        print("Components (edges):")
        for u, v, data in self._graph.edges(data=True):
            ctype = data.get("type", "?")
            cname = data.get("name", "?")
            val = _format_value(data.get("value"), ctype)
            print(f"  {cname}: {u} ── {v}  [{ctype}] {val}")
        print()

        # Series chains
        chains = self.FindSeriesChains()
        if chains:
            print("Series chains:")
            for chain in chains:
                comps = []
                for a, b in zip(chain[:-1], chain[1:]):
                    for _, edata in self._graph[a][b].items():
                        comps.append(edata["name"])
                print(f"  {' → '.join(chain)}  ({', '.join(comps)})")
            print()

        # Parallel groups
        parallels = self.FindParallelComponents()
        if parallels:
            print("Parallel groups:")
            for u, v, edges in parallels:
                names = [e["name"] for e in edges]
                print(f"  {u} ═══ {v}: {', '.join(names)}")
            print()

    def __repr__(self) -> str:
        return (f"CircuitGraph(nodes={self._graph.number_of_nodes()}, "
                f"edges={self._graph.number_of_edges()})")
