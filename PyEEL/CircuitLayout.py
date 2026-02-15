"""
CircuitLayout — pattern-aware 2D layout engine for circuit graphs.

Converts a :class:`CircuitGraph` into a dictionary of node positions
suitable for rendering with schemdraw.  The engine works in three
passes:

1. **Pattern recognition** — detect known topologies (series loop,
   voltage divider, parallel branches, filter networks).
2. **Position assignment** — apply topology-specific placement or fall
   back to a hierarchical / spring layout.
3. **Grid snapping** — round all positions to the nearest grid point
   for clean, readable schematics.

Usage
-----
::

    from PyEEL.CircuitGraph import CircuitGraph
    from PyEEL.CircuitLayout import CircuitLayout

    graph  = CircuitGraph(ckt)
    layout = CircuitLayout(graph)
    layout.Summary()

    positions = layout.Positions     # {node_name: (x, y)}
    pattern   = layout.Pattern       # detected topology name
    draw_order = layout.DrawOrder    # ordered list of (comp_name, from, to, direction)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

import networkx as nx

from .CircuitGraph import CircuitGraph, _format_value


# ════════════════════════════════════════════════════════════════════
#  Pattern enumeration
# ════════════════════════════════════════════════════════════════════
class TopologyPattern(Enum):
    """Recognised circuit topology patterns."""
    SERIES_LOOP     = auto()   # single loop: source + series components
    VOLTAGE_DIVIDER = auto()   # source + 2 resistors, output tap
    PARALLEL_RC     = auto()   # R ∥ C between two nodes
    PARALLEL_RL     = auto()   # R ∥ L between two nodes
    PARALLEL_LC     = auto()   # L ∥ C between two nodes
    LADDER          = auto()   # alternating series / shunt sections
    WHEATSTONE      = auto()   # 4-resistor bridge
    GENERIC         = auto()   # no known pattern matched


@dataclass
class DrawStep:
    """One rendering instruction for the schematic drawer."""
    comp_name: str          # e.g. "R1"
    comp_type: str          # e.g. "R"
    from_node: str          # start node name
    to_node: str            # end node name
    direction: str          # "right", "down", "left", "up"
    value: float | None = None
    extra: dict = field(default_factory=dict)   # waveform info etc.


# ════════════════════════════════════════════════════════════════════
#  Layout engine
# ════════════════════════════════════════════════════════════════════
class CircuitLayout:
    """
    Compute 2D node positions and drawing order for a circuit graph.

    Parameters
    ----------
    graph : CircuitGraph
        The circuit graph to lay out.
    grid : float
        Grid spacing for snapping (default 3.0 — one schemdraw element).
    """

    _graph: CircuitGraph
    _grid: float
    _positions: dict[str, tuple[float, float]]
    _pattern: TopologyPattern
    _draw_order: list[DrawStep]

    def __init__(self, graph: CircuitGraph, grid: float = 3.0):
        self._graph = graph
        self._grid = grid
        self._positions = {}
        self._draw_order = []

        # Run the pipeline
        self._pattern = self._detect_pattern()
        self._compute_positions()
        self._snap_to_grid()

    # ── public API ──────────────────────────────────────────────────
    @property
    def Positions(self) -> dict[str, tuple[float, float]]:
        """Node name → (x, y) positions on the schematic grid."""
        return dict(self._positions)

    @property
    def Pattern(self) -> TopologyPattern:
        """The topology pattern that was detected."""
        return self._pattern

    @property
    def DrawOrder(self) -> list[DrawStep]:
        """Ordered list of draw instructions for the renderer."""
        return list(self._draw_order)

    @property
    def GroundNode(self) -> str:
        """Name of the ground node."""
        return self._graph.GroundNode

    @property
    def Grid(self) -> float:
        """Grid spacing used for snapping (schemdraw units)."""
        return self._grid

    # ════════════════════════════════════════════════════════════════
    #  Pass 1: Pattern Recognition
    # ════════════════════════════════════════════════════════════════
    def _detect_pattern(self) -> TopologyPattern:
        """Classify the circuit topology."""
        G = self._graph.Graph
        n_nodes = G.number_of_nodes()
        n_edges = G.number_of_edges()
        deg_map = dict(G.degree())  # type: ignore[operator]

        gnd = self._graph.GroundNode
        parallels = self._graph.FindParallelComponents()

        # ── Wheatstone bridge ───────────────────────────────────────
        # 4 non-GND nodes forming a diamond + source across one diagonal
        if self._is_wheatstone(deg_map, gnd):
            return TopologyPattern.WHEATSTONE

        # ── Parallel branches (R∥C, R∥L, L∥C) ──────────────────────
        if parallels and n_edges <= 5:
            # Collect non-source types in the parallel group
            types_in_parallel = set()
            for _, _, edges in parallels:
                for e in edges:
                    t = e.get("type")
                    if t != "V":          # exclude the source
                        types_in_parallel.add(t)
            if types_in_parallel == {"R", "C"}:
                return TopologyPattern.PARALLEL_RC
            if types_in_parallel == {"R", "L"}:
                return TopologyPattern.PARALLEL_RL
            if types_in_parallel == {"L", "C"}:
                return TopologyPattern.PARALLEL_LC

        # ── Voltage divider ─────────────────────────────────────────
        # Source + exactly 2 resistors in series from source node to GND
        if self._is_voltage_divider(deg_map, gnd):
            return TopologyPattern.VOLTAGE_DIVIDER

        # ── Series loop ─────────────────────────────────────────────
        # All nodes degree 2 → single loop
        if all(d == 2 for d in deg_map.values()):
            return TopologyPattern.SERIES_LOOP

        # ── Ladder network ──────────────────────────────────────────
        if self._is_ladder(deg_map, gnd):
            return TopologyPattern.LADDER

        return TopologyPattern.GENERIC

    # ── individual pattern detectors ────────────────────────────────
    def _is_voltage_divider(self, deg_map: dict, gnd: str) -> bool:
        """
        Voltage divider: source between node_a and GND, then exactly
        two resistors in series from node_a through node_mid to GND.
        """
        G = self._graph.Graph
        sources = self._graph.ComponentsByType("V")
        resistors = self._graph.ComponentsByType("R")

        if len(sources) != 1 or len(resistors) != 2:
            return False

        src = sources[0]
        src_nodes = {src["from"], src["to"]}
        if gnd not in src_nodes:
            return False

        # The non-GND source node
        src_node = (src_nodes - {gnd}).pop()

        # Check: is there a path src_node → mid → GND through exactly
        # the 2 resistors, with mid having degree 2?
        r_nodes = set()
        for r in resistors:
            r_nodes.add(r["from"])
            r_nodes.add(r["to"])

        mid_candidates = r_nodes - {gnd, src_node}
        if len(mid_candidates) != 1:
            return False

        mid = mid_candidates.pop()
        return deg_map.get(mid, 0) == 2

    def _is_wheatstone(self, deg_map: dict, gnd: str) -> bool:
        """
        Wheatstone bridge: 4+ resistors (including galvanometer) + source
        forming a diamond.  Accepts 3 or 4 non-GND nodes.
        """
        G = self._graph.Graph
        non_gnd = [n for n in G.nodes if n != gnd]

        if len(non_gnd) < 3 or len(non_gnd) > 5:
            return False

        resistors = self._graph.ComponentsByType("R")
        sources = self._graph.ComponentsByType("V")

        # Need at least 4 resistors + 1 source (classic bridge +
        # galvanometer, with GND acting as one node of the diamond).
        if not (len(resistors) >= 4 and len(sources) >= 1):
            return False

        # At least 2 non-GND nodes with degree >= 3
        deg3_count = sum(1 for n in non_gnd if deg_map.get(n, 0) >= 3)
        return deg3_count >= 2

    def _is_ladder(self, deg_map: dict, gnd: str) -> bool:
        """
        Ladder network: alternating series and shunt elements.
        GND has degree >= 2 (shunt connections), and there are at
        least 2 non-GND nodes connected by series elements along
        a top rail, with shunt elements dropping to GND.
        """
        gnd_deg = deg_map.get(gnd, 0)
        if gnd_deg < 2:
            return False

        G = self._graph.Graph
        non_gnd = [n for n in G.nodes if n != gnd]

        # Need at least 3 non-GND nodes for a meaningful ladder
        if len(non_gnd) < 3:
            return False

        # Check that at least 2 non-GND nodes connect to GND
        # (shunt elements)
        shunt_count = sum(
            1 for n in non_gnd
            if G.has_edge(n, gnd) or G.has_edge(gnd, n)
        )
        if shunt_count < 2:
            return False

        # Check for series elements between consecutive top-rail nodes
        series_count = 0
        for n in non_gnd:
            for nb in G.neighbors(n):
                if nb != gnd and nb in non_gnd:
                    series_count += 1
        # Each edge counted twice (undirected), need at least 2 edges
        return series_count >= 4  # 2 series edges × 2 directions

    # ════════════════════════════════════════════════════════════════
    #  Pass 2: Position assignment
    # ════════════════════════════════════════════════════════════════
    def _compute_positions(self) -> None:
        """Dispatch to the appropriate layout method."""
        dispatch = {
            TopologyPattern.SERIES_LOOP:     self._layout_series_loop,
            TopologyPattern.VOLTAGE_DIVIDER: self._layout_voltage_divider,
            TopologyPattern.PARALLEL_RC:     self._layout_parallel,
            TopologyPattern.PARALLEL_RL:     self._layout_parallel,
            TopologyPattern.PARALLEL_LC:     self._layout_parallel,
            TopologyPattern.LADDER:          self._layout_ladder,
            TopologyPattern.WHEATSTONE:      self._layout_wheatstone,
            TopologyPattern.GENERIC:         self._layout_generic,
        }
        dispatch[self._pattern]()

    # ── Series loop ─────────────────────────────────────────────────
    def _layout_series_loop(self) -> None:
        """
        Single-loop circuit: source on the left (vertical), series
        components across the top, return wire along the bottom.

        ```
            (src+) ── C1 ──── C2 ──── C3 ── (last)
              │                                │
            [SRC]                             [wire]
              │                                │
            (GND) ──────── bottom rail ──────(GND)
        ```
        """
        G = self._graph.Graph
        gnd = self._graph.GroundNode

        # Find the source and build the series order
        chain = self._build_ordered_chain(gnd)
        if not chain:
            self._layout_generic()
            return

        # chain: [GND, n_src, ..., n_last, GND]
        # The source is the edge GND↔n_src (first edge)
        # Series components are the remaining edges

        n = len(chain) - 1  # number of edges in the chain
        # Source occupies left side (vertical), other components go right

        # Source node positions
        width = max(n - 1, 1)  # horizontal span for series components
        self._positions[gnd] = (0.0, 0.0)

        # Place nodes along the chain
        # chain[0] = GND (bottom-left)
        # chain[1] = source+ node (top-left)
        # chain[2..n-1] = intermediate nodes (across top)
        # chain[n] = GND again (bottom-right, same as chain[0])

        for i, node in enumerate(chain):
            if node == gnd:
                continue
            if i == 1:
                # Source positive terminal — top-left
                self._positions[node] = (0.0, 1.0)
            else:
                # Series components across the top
                x = float(i - 1)
                self._positions[node] = (x, 1.0)

        # Build draw order
        self._draw_order.clear()
        for i in range(len(chain) - 1):
            n1, n2 = chain[i], chain[i + 1]
            edges = self._graph.ComponentsBetween(n1, n2)
            if not edges:
                # Try reversed
                edges = self._graph.ComponentsBetween(n2, n1)
                if edges:
                    n1, n2 = n2, n1
            if not edges:
                continue

            edge = edges[0]
            comp_name = edge["name"]
            comp_type = edge["type"]

            # Determine direction from positions
            if i == 0:
                direction = "up"      # source goes up
            elif i == len(chain) - 2:
                direction = "down"    # last component returns down
            else:
                direction = "right"   # series across top

            self._draw_order.append(DrawStep(
                comp_name=comp_name,
                comp_type=comp_type,
                from_node=n1,
                to_node=n2,
                direction=direction,
                value=edge.get("value"),
                extra={k: v for k, v in edge.items()
                       if k not in ("component", "name", "type", "value")},
            ))

    def _build_ordered_chain(self, gnd: str) -> list[str]:
        """
        Walk around a single-loop circuit starting from GND, preferring
        to start with a voltage source edge.

        Returns [GND, n1, n2, ..., n_last, GND].
        """
        G = self._graph.Graph
        neighbors = list(G.neighbors(gnd))
        if len(neighbors) < 1:
            return []

        # Prefer to start with the voltage source edge
        start_neighbor = neighbors[0]
        for nb in neighbors:
            for _, edata in G[gnd][nb].items():
                if edata.get("type") == "V":
                    start_neighbor = nb
                    break

        # Walk the loop
        chain = [gnd, start_neighbor]
        prev, curr = gnd, start_neighbor
        visited = {gnd}

        while True:
            visited.add(curr)
            nbrs = [n for n in G.neighbors(curr) if n != prev or n == gnd]
            next_node = None
            for n in nbrs:
                if n == gnd and len(chain) > 2:
                    # Closing the loop
                    chain.append(gnd)
                    return chain
                if n not in visited:
                    next_node = n
                    break

            if next_node is None:
                # Dead end or back to start
                if gnd in nbrs and len(chain) > 2:
                    chain.append(gnd)
                return chain

            chain.append(next_node)
            prev, curr = curr, next_node

        return chain

    # ── Voltage divider ─────────────────────────────────────────────
    def _layout_voltage_divider(self) -> None:
        """
        ```
            (src+) ─── R1 ─── (mid) ─── R2 ─── (GND)
              │                  ↑ output        │
            [SRC]                                │
              │                                  │
            (GND) ─────────────────────────────(GND)
        ```
        Layout as an L-shape: source left, R1 top, R2 right-down.
        """
        gnd = self._graph.GroundNode
        sources = self._graph.ComponentsByType("V")
        resistors = self._graph.ComponentsByType("R")
        src = sources[0]

        src_nodes = {src["from"], src["to"]}
        src_node = (src_nodes - {gnd}).pop()

        # Find mid node (degree-2 node between the two resistors)
        r_nodes = set()
        for r in resistors:
            r_nodes.update({r["from"], r["to"]})
        mid = (r_nodes - {gnd, src_node}).pop()

        self._positions[gnd] = (0.0, 0.0)
        self._positions[src_node] = (0.0, 1.0)
        self._positions[mid] = (1.0, 1.0)

        # Draw order: source up, R1 right, R2 down
        self._draw_order = [
            DrawStep(src["name"], "V", gnd, src_node, "up",
                     src.get("value"),
                     {k: v for k, v in src.items()
                      if k not in ("component", "name", "type", "value", "from", "to")}),
            DrawStep(resistors[0]["name"], "R", src_node, mid, "right",
                     resistors[0].get("value")),
            DrawStep(resistors[1]["name"], "R", mid, gnd, "down",
                     resistors[1].get("value")),
        ]

    # ── Parallel branches ───────────────────────────────────────────
    def _layout_parallel(self) -> None:
        """
        Circuit with parallel components between two nodes + source.

        ```
            (n+) ─── comp_a ─── (n−)
              │                   │
              └── comp_b ─────────┘
        ```
        """
        gnd = self._graph.GroundNode
        parallels = self._graph.FindParallelComponents()

        # Find source
        sources = self._graph.ComponentsByType("V")
        src = sources[0] if sources else None

        if src:
            src_nodes = {src["from"], src["to"]}
            src_node = (src_nodes - {gnd}).pop() if gnd in src_nodes else list(src_nodes)[0]
        else:
            src_node = [n for n in self._graph.Nodes if n != gnd][0]

        # Parallel pair nodes
        if parallels:
            pa, pb = parallels[0][0], parallels[0][1]
            par_edges = parallels[0][2]
        else:
            self._layout_generic()
            return

        # Figure out which node connects to source
        if pa == gnd or pb == gnd:
            top_node = pa if pa != gnd else pb
        else:
            top_node = pa

        self._positions[gnd] = (0.0, 0.0)
        if src:
            self._positions[src_node] = (0.0, 1.0)

        # Position the parallel pair
        if top_node not in self._positions:
            self._positions[top_node] = (1.0, 1.0)
        other_par = pb if pa == top_node else pa
        if other_par not in self._positions:
            self._positions[other_par] = (2.0, 1.0)

        # Draw order
        self._draw_order.clear()
        if src:
            self._draw_order.append(DrawStep(
                src["name"], "V", gnd, src_node, "up", src.get("value"),
                {k: v for k, v in src.items()
                 if k not in ("component", "name", "type", "value", "from", "to")}))

        # Series components from source to parallel junction
        chain = self._graph.FindSeriesChains()
        for ch in chain:
            for i in range(len(ch) - 1):
                a, b = ch[i], ch[i + 1]
                edges = self._graph.ComponentsBetween(a, b)
                if not edges:
                    edges = self._graph.ComponentsBetween(b, a)
                for e in edges:
                    if e["name"] == (src["name"] if src else ""):
                        continue
                    if any(ds.comp_name == e["name"] for ds in self._draw_order):
                        continue
                    self._draw_order.append(DrawStep(
                        e["name"], e["type"], a, b, "right", e.get("value")))

        # Parallel components
        for i, e in enumerate(par_edges):
            if any(ds.comp_name == e["name"] for ds in self._draw_order):
                continue
            d = "right" if i == 0 else "down"
            self._draw_order.append(DrawStep(
                e["name"], e["type"], pa, pb, d, e.get("value")))

    # ── Ladder network ──────────────────────────────────────────────
    def _layout_ladder(self) -> None:
        """
        ```
        (n1) ─── Z1 ─── (n2) ─── Z3 ─── (n3)
                          │                │
                         Z2               Z4
                          │                │
                        (GND) ──────── (GND)
        ```
        """
        gnd = self._graph.GroundNode
        G = self._graph.Graph

        # Build top-rail chain: start from a source node, walk non-GND
        sources = self._graph.ComponentsByType("V")
        src: dict | None = sources[0] if sources else None
        if src:
            src_nodes = {src["from"], src["to"]}
            start = (src_nodes - {gnd}).pop() if gnd in src_nodes else list(src_nodes)[0]
        else:
            start = [n for n in G.nodes if n != gnd][0]

        # Walk the top rail (non-GND neighbors)
        top_rail = [start]
        visited = {gnd, start}
        curr = start
        while True:
            nbrs = [n for n in G.neighbors(curr) if n not in visited and n != gnd]
            if not nbrs:
                break
            curr = nbrs[0]
            top_rail.append(curr)
            visited.add(curr)

        # Position top rail
        self._positions[gnd] = (0.0, 0.0)
        for i, node in enumerate(top_rail):
            self._positions[node] = (float(i), 1.0)

        # Draw order
        self._draw_order.clear()

        # Source
        drawn: set[str] = set()
        if src is not None:
            self._draw_order.append(DrawStep(
                src["name"], "V", gnd, start, "up", src.get("value"),
                {k: v for k, v in src.items()
                 if k not in ("component", "name", "type", "value", "from", "to")}))
            drawn.add(src["name"])

        # Series elements along top rail
        for i in range(len(top_rail) - 1):
            a, b = top_rail[i], top_rail[i + 1]
            edges = self._graph.ComponentsBetween(a, b)
            if not edges:
                edges = self._graph.ComponentsBetween(b, a)
            for e in edges:
                if e["name"] not in drawn:
                    self._draw_order.append(DrawStep(
                        e["name"], e["type"], a, b, "right", e.get("value")))
                    drawn.add(e["name"])

        # Shunt elements (to GND)
        for node in top_rail:
            edges = self._graph.ComponentsBetween(node, gnd)
            if not edges:
                edges = self._graph.ComponentsBetween(gnd, node)
            for e in edges:
                if e["name"] not in drawn:
                    self._draw_order.append(DrawStep(
                        e["name"], e["type"], node, gnd, "down", e.get("value")))
                    drawn.add(e["name"])

    # ── Wheatstone bridge ───────────────────────────────────────────
    def _layout_wheatstone(self) -> None:
        """
        Diamond layout for a Wheatstone bridge.  GND acts as the bottom
        corner if there are only 3 non-GND nodes.

        ```
              (src)
             /     \\
          R1         R3
           /           \\
        (mid_a) ─ Rg ─ (mid_b)
           \\           /
          R2         R4
             \\     /
              (GND)
        ```
        """
        gnd = self._graph.GroundNode
        G = self._graph.Graph
        deg_map = dict(G.degree())  # type: ignore[operator]

        non_gnd = sorted(
            [n for n in G.nodes if n != gnd],
            key=lambda n: deg_map[n], reverse=True
        )

        # Place in diamond — GND is always the bottom corner
        self._positions[gnd] = (1.0, 0.0)

        if len(non_gnd) >= 3:
            # Highest degree node = source (top), next two = midpoints
            self._positions[non_gnd[0]] = (1.0, 2.0)   # top (source node)
            self._positions[non_gnd[1]] = (0.0, 1.0)   # left midpoint
            self._positions[non_gnd[2]] = (2.0, 1.0)   # right midpoint

        if len(non_gnd) >= 4:
            self._positions[non_gnd[3]] = (1.0, 0.0)   # extra bottom
            self._positions[gnd] = (1.0, -1.0)

        # Draw order: enumerate all edges
        self._draw_order.clear()
        for u, v, data in G.edges(data=True):
            p1 = self._positions.get(u, (0, 0))
            p2 = self._positions.get(v, (0, 0))
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            if abs(dx) >= abs(dy):
                direction = "right" if dx >= 0 else "left"
            else:
                direction = "up" if dy >= 0 else "down"

            self._draw_order.append(DrawStep(
                comp_name=data["name"],
                comp_type=data["type"],
                from_node=u,
                to_node=v,
                direction=direction,
                value=data.get("value"),
                extra={k: v_ for k, v_ in data.items()
                       if k not in ("component", "name", "type", "value")},
            ))

    # ── Generic fallback ────────────────────────────────────────────
    def _layout_generic(self) -> None:
        """
        Use hierarchical layering if the graph is a DAG-like structure,
        otherwise fall back to a spring layout.
        """
        G = self._graph.Graph
        gnd = self._graph.GroundNode

        # Try hierarchical: assign layers by BFS distance from GND
        layers = self._bfs_layers(gnd)

        if layers:
            self._layout_from_layers(layers)
        else:
            self._layout_spring()

    def _bfs_layers(self, root: str) -> dict[str, int] | None:
        """
        Assign each node a layer (distance from *root*) via BFS.
        Returns None if the graph is disconnected from root.
        """
        G = self._graph.Graph
        if root not in G:
            return None

        layers: dict[str, int] = {}
        queue = [root]
        layers[root] = 0

        while queue:
            curr = queue.pop(0)
            for nb in G.neighbors(curr):
                if nb not in layers:
                    layers[nb] = layers[curr] + 1
                    queue.append(nb)

        # Check all nodes reached
        if len(layers) != G.number_of_nodes():
            return None

        return layers

    def _layout_from_layers(self, layers: dict[str, int]) -> None:
        """Position nodes in a hierarchical layout based on BFS layers."""
        # Group by layer
        by_layer: dict[int, list[str]] = {}
        for node, layer in layers.items():
            by_layer.setdefault(layer, []).append(node)

        # Position: layer = y, index within layer = x
        for layer_num, nodes in sorted(by_layer.items()):
            n = len(nodes)
            for i, node in enumerate(nodes):
                x = float(i) - (n - 1) / 2.0   # center horizontally
                y = float(layer_num)
                self._positions[node] = (x, y)

        # Build draw order from edges
        self._draw_order.clear()
        G = self._graph.Graph
        for u, v, data in G.edges(data=True):
            p1 = self._positions.get(u, (0, 0))
            p2 = self._positions.get(v, (0, 0))
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            if abs(dx) >= abs(dy):
                direction = "right" if dx >= 0 else "left"
            else:
                direction = "up" if dy >= 0 else "down"

            self._draw_order.append(DrawStep(
                comp_name=data["name"],
                comp_type=data["type"],
                from_node=u, to_node=v,
                direction=direction,
                value=data.get("value"),
                extra={k: v_ for k, v_ in data.items()
                       if k not in ("component", "name", "type", "value")},
            ))

    def _layout_spring(self) -> None:
        """Last-resort spring layout via NetworkX."""
        G = self._graph.Graph
        pos = nx.spring_layout(G, seed=42)
        # Scale up from [0,1]² to grid units
        max_dim = max(
            max(abs(p[0]) for p in pos.values()),
            max(abs(p[1]) for p in pos.values()),
            0.01
        )
        scale = float(len(G.nodes))
        for node, (x, y) in pos.items():
            self._positions[node] = (x / max_dim * scale, y / max_dim * scale)

        # Build draw order
        self._draw_order.clear()
        for u, v, data in G.edges(data=True):
            p1 = self._positions.get(u, (0, 0))
            p2 = self._positions.get(v, (0, 0))
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            if abs(dx) >= abs(dy):
                direction = "right" if dx >= 0 else "left"
            else:
                direction = "up" if dy >= 0 else "down"

            self._draw_order.append(DrawStep(
                comp_name=data["name"],
                comp_type=data["type"],
                from_node=u, to_node=v,
                direction=direction,
                value=data.get("value"),
                extra={k: v_ for k, v_ in data.items()
                       if k not in ("component", "name", "type", "value")},
            ))

    # ════════════════════════════════════════════════════════════════
    #  Pass 3: Grid snapping
    # ════════════════════════════════════════════════════════════════
    def _snap_to_grid(self) -> None:
        """Round all positions to the nearest grid point."""
        g = self._grid
        snapped: dict[str, tuple[float, float]] = {}
        for node, (x, y) in self._positions.items():
            sx = round(x * g) / g * g   # snap x to grid
            sy = round(y * g) / g * g   # snap y to grid
            # Simplify: multiply by grid, round, keep as grid multiples
            sx = round(x) * g
            sy = round(y) * g
            snapped[node] = (sx, sy)

        # Resolve collisions: nudge overlapping nodes
        occupied: dict[tuple[float, float], str] = {}
        for node, pos in snapped.items():
            while pos in occupied:
                pos = (pos[0] + g, pos[1])
            occupied[pos] = node
            snapped[node] = pos

        self._positions = snapped

    # ════════════════════════════════════════════════════════════════
    #  Output
    # ════════════════════════════════════════════════════════════════
    def Summary(self) -> None:
        """Print layout summary including pattern and positions."""
        print(f"CircuitLayout: pattern = {self._pattern.name}")
        print()

        print("Node positions (grid-snapped):")
        for node, (x, y) in sorted(self._positions.items()):
            gnd = " (GND)" if node == self._graph.GroundNode else ""
            print(f"  {node}{gnd}: ({x:.1f}, {y:.1f})")
        print()

        print(f"Draw order ({len(self._draw_order)} steps):")
        for i, step in enumerate(self._draw_order):
            val = _format_value(step.value, step.comp_type)
            print(f"  {i + 1}. [{step.comp_type}] {step.comp_name} "
                  f"{step.from_node} → {step.to_node} "
                  f"({step.direction}) {val}")
        print()

    def __repr__(self) -> str:
        return (f"CircuitLayout(pattern={self._pattern.name}, "
                f"nodes={len(self._positions)}, "
                f"steps={len(self._draw_order)})")
