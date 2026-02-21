"""
SchematicDrawer — render a circuit schematic with schemdraw.

This is the **rendering layer** of the PyEEL visualization pipeline::

    Circuit  →  CircuitGraph  →  CircuitLayout  →  SchematicDrawer
     (MNA)       (topology)      (positions)       (schemdraw figure)

The drawer consumes a :class:`CircuitLayout` (positions + draw order)
and produces a ``schemdraw.Drawing`` that can be displayed interactively
or saved to PNG / SVG / PDF.

Usage
-----
::

    from PyEEL.CircuitGraph import CircuitGraph
    from PyEEL.CircuitLayout import CircuitLayout
    from PyEEL.SchematicDrawer import SchematicDrawer

    graph  = CircuitGraph(ckt)
    layout = CircuitLayout(graph)
    drawer = SchematicDrawer(layout)
    drawer.Draw()                   # interactive matplotlib window
    drawer.Save("schematic.png")    # file output

One-liner shortcut::

    SchematicDrawer.FromCircuit(ckt).Draw()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import schemdraw
import schemdraw.elements as elm

from .CircuitLayout import CircuitLayout, DrawStep
from .CircuitGraph import _format_value

if TYPE_CHECKING:
    from .Circuit import Circuit


# ── element mapping ─────────────────────────────────────────────────
_ELEMENT_MAP: dict[str, type] = {
    "R": elm.Resistor,
    "C": elm.Capacitor,
    "L": elm.Inductor,
    "V": elm.SourceV,
}


# ════════════════════════════════════════════════════════════════════
class SchematicDrawer:
    """
    Render a :class:`CircuitLayout` as a schemdraw schematic.

    Parameters
    ----------
    layout : CircuitLayout
        Pre-computed layout with node positions and draw order.
    """

    _layout: CircuitLayout
    _drawing: schemdraw.Drawing | None

    def __init__(self, layout: CircuitLayout):
        self._layout = layout
        self._drawing = None

    # ── convenience constructor ─────────────────────────────────────
    @staticmethod
    def FromCircuit(
        circuit: "Circuit", grid: float = 3.0
    ) -> "SchematicDrawer":
        """
        Build the full pipeline in one call.

        ``Circuit → CircuitGraph → CircuitLayout → SchematicDrawer``
        """
        from .CircuitGraph import CircuitGraph

        graph = CircuitGraph(circuit)
        layout = CircuitLayout(graph, grid=grid)
        return SchematicDrawer(layout)

    # ── public API ──────────────────────────────────────────────────
    @property
    def Drawing(self) -> schemdraw.Drawing:
        """The underlying ``schemdraw.Drawing`` (built lazily)."""
        if self._drawing is None:
            self._drawing = self._build()
        return self._drawing

    def Draw(self, *, show: bool = True) -> None:
        """
        Display the schematic in a matplotlib window.

        Parameters
        ----------
        show : bool
            If *True* (default), call ``plt.show()`` to display the
            window.  Set to *False* to create the figure without
            blocking.
        """
        self.Drawing.draw(show=show)

    def Save(self, path: str, *, dpi: int = 150) -> None:
        """
        Save the schematic to a file.

        Supported formats: PNG, SVG, PDF — anything matplotlib can
        write.
        """
        self.Drawing.save(path, dpi=dpi)

    # ════════════════════════════════════════════════════════════════
    #  Drawing construction
    # ════════════════════════════════════════════════════════════════
    def _build(self) -> schemdraw.Drawing:
        """Assemble the ``schemdraw.Drawing`` from layout data."""
        from .CircuitLayout import TopologyPattern

        pattern = self._layout.Pattern
        if pattern in (TopologyPattern.PARALLEL_RC,
                       TopologyPattern.PARALLEL_RL,
                       TopologyPattern.PARALLEL_LC):
            return self._build_parallel()
        if pattern == TopologyPattern.WHEATSTONE:
            return self._build_wheatstone()
        return self._build_positioned()

    # ── position-based build (most topologies) ──────────────────────
    def _build_positioned(self) -> schemdraw.Drawing:
        """Standard build using absolute node positions."""
        d = schemdraw.Drawing(unit=self._layout.Grid)

        positions = self._layout.Positions
        draw_order = self._layout.DrawOrder
        gnd = self._layout.GroundNode

        used_mids: set[tuple[float, float]] = set()

        # ── components ──────────────────────────────────────────────
        for step in draw_order:
            if step.comp_type == "W":   # internal wire marker
                continue

            p1 = positions.get(step.from_node, (0.0, 0.0))
            p2 = positions.get(step.to_node, (0.0, 0.0))

            element = self._create_element(step)
            label = self._make_label(step)
            loc = self._pick_label_loc(step.direction)

            if self._is_aligned(p1, p2):
                element.at(p1).to(p2)
                if label:
                    element.label(label, loc=loc)
                d += element
            else:
                mid = self._route_intermediate(p1, p2, step.direction)
                # Offset colliding intermediate points
                grid = self._layout.Grid
                while mid in used_mids:
                    if step.direction in ("up", "down"):
                        mid = (mid[0] + grid * 0.4, mid[1])
                    else:
                        mid = (mid[0], mid[1] + grid * 0.4)
                used_mids.add(mid)

                element.at(p1).to(mid)
                if label:
                    element.label(label, loc=loc)
                d += element
                d += elm.Line().at(mid).to(p2)

        # ── ground symbol ───────────────────────────────────────────
        gnd_pos = positions.get(gnd)
        if gnd_pos is not None:
            d += elm.Ground().at(gnd_pos)

        # ── junction dots (nodes touched by 3+ component legs) ──────
        touch: dict[str, int] = {}
        for step in draw_order:
            if step.comp_type == "W":
                continue
            touch[step.from_node] = touch.get(step.from_node, 0) + 1
            touch[step.to_node] = touch.get(step.to_node, 0) + 1

        for node, count in touch.items():
            if count > 2 and node != gnd:
                pos = positions.get(node)
                if pos is not None:
                    d += elm.Dot().at(pos)

        return d

    # ── parallel build (chain-based, no coordinate overlap) ─────────
    def _build_parallel(self) -> schemdraw.Drawing:
        """
        Draw parallel circuits using schemdraw's sequential placement.

        Layout::

            ┌──────── R1 ────────┐
            │                    │
            ├──────── C1 ────────┤
            │                    │
            V1 (source)          │
            │                    │
           ─┴─ GND              │
        """
        d = schemdraw.Drawing(unit=self._layout.Grid)
        grid = self._layout.Grid
        draw_order = self._layout.DrawOrder
        gnd_name = self._layout.GroundNode

        # Separate source step from passive steps
        src_step: DrawStep | None = None
        passive_steps: list[DrawStep] = []
        for step in draw_order:
            if step.comp_type == "W":
                continue
            if step.comp_type == "V":
                src_step = step
            else:
                passive_steps.append(step)

        n = len(passive_steps)
        width = max(n, 1) * grid    # total horizontal span

        # Source on the left, going up
        if src_step:
            src_elem = self._create_element(src_step)
            src_label = self._make_label(src_step)
            src_elem.at((0.0, 0.0)).up()
            if src_label:
                src_elem.label(src_label, loc="right")
            d += src_elem

        # Top rail: wire from source top to the right
        top_left = (0.0, grid)
        top_right = (width, grid)
        d += elm.Line().at(top_left).to(top_right)

        # Each passive component drops vertically
        for i, step in enumerate(passive_steps):
            x = (i + 1) * grid
            comp_top = (x, grid)
            comp_bot = (x, 0.0)

            elem = self._create_element(step)
            label = self._make_label(step)
            elem.at(comp_top).to(comp_bot)
            if label:
                elem.label(label)
            d += elem

        # Bottom rail: wire from rightmost passive back to source bottom
        bot_right = (width, 0.0)
        bot_left = (0.0, 0.0)
        d += elm.Line().at(bot_right).to(bot_left)

        # Ground at source bottom
        d += elm.Ground().at(bot_left)

        # Junction dots at top/bottom rails
        if n > 0:
            d += elm.Dot().at(top_left)
            if n > 1:
                for i in range(n - 1):
                    d += elm.Dot().at(((i + 1) * grid, grid))

        return d

    # ── Wheatstone bridge build (diamond + external source) ─────────
    def _build_wheatstone(self) -> schemdraw.Drawing:
        """
        Draw a Wheatstone bridge with the source routed outside the
        diamond so it never crosses the galvanometer.

        Layout::

            (tl) ─── R_TL ─── top ─── R_TR ─── (tr)
              │                 .                 │
              │            (V1 external)          │
             n_L ──────── Rg ──────── n_R
              │                                   │
             R_BL                                R_BR
              │                                   │
            (bl) ──────── GND ──────────── (br)
        """
        d = schemdraw.Drawing(unit=self._layout.Grid)
        grid = self._layout.Grid
        positions = self._layout.Positions
        draw_order = self._layout.DrawOrder
        gnd_name = self._layout.GroundNode

        # ── identify node roles from positions ──────────────────────
        pos_items = [(n, p) for n, p in positions.items()]

        # Top node = highest y (source terminal, usually highest degree)
        top_node = max(pos_items, key=lambda kv: kv[1][1])[0]
        top_pos = positions[top_node]

        # Bottom node = GND
        bot_node = gnd_name
        bot_pos = positions[bot_node]

        # Middle nodes sorted by x → left, right
        mid_entries = sorted(
            [(n, p) for n, p in pos_items
             if n != top_node and n != bot_node],
            key=lambda kv: kv[1][0],
        )
        left_node = mid_entries[0][0]
        left_pos = mid_entries[0][1]
        right_node = mid_entries[-1][0]
        right_pos = mid_entries[-1][1]

        # ── corner coordinates ──────────────────────────────────────
        tl = (left_pos[0], top_pos[1])
        tr = (right_pos[0], top_pos[1])
        bl = (left_pos[0], bot_pos[1])
        br = (right_pos[0], bot_pos[1])

        # Source lives one grid unit to the left of the diamond
        src_top = (left_pos[0] - grid, top_pos[1])
        src_bot = (left_pos[0] - grid, bot_pos[1])

        # ── categorise components ───────────────────────────────────
        comp: dict[str, DrawStep] = {}
        extras: list[DrawStep] = []

        for step in draw_order:
            if step.comp_type == "W":
                continue
            nodes = frozenset({step.from_node, step.to_node})
            if step.comp_type == "V":
                comp["SRC"] = step
            elif nodes == frozenset({top_node, left_node}):
                comp["TL"] = step
            elif nodes == frozenset({top_node, right_node}):
                comp["TR"] = step
            elif nodes == frozenset({left_node, bot_node}):
                comp["BL"] = step
            elif nodes == frozenset({right_node, bot_node}):
                comp["BR"] = step
            elif nodes == frozenset({left_node, right_node}):
                comp["MID"] = step
            else:
                extras.append(step)

        # ── draw source on external left path ───────────────────────
        if "SRC" in comp:
            step = comp["SRC"]
            d += elm.Line().at(top_pos).to(src_top)
            elem = self._create_element(step)
            label = self._make_label(step)
            elem.at(src_top).to(src_bot)
            if label:
                elem.label(label, loc="left")
            d += elem
            d += elm.Line().at(src_bot).to(bot_pos)

        # ── top-left arm: horizontal at top level, wire down ────────
        if "TL" in comp:
            step = comp["TL"]
            elem = self._create_element(step)
            label = self._make_label(step)
            elem.at(top_pos).to(tl)
            if label:
                elem.label(label, loc="top")
            d += elem
            d += elm.Line().at(tl).to(left_pos)

        # ── top-right arm: horizontal at top level, wire down ───────
        if "TR" in comp:
            step = comp["TR"]
            elem = self._create_element(step)
            label = self._make_label(step)
            elem.at(top_pos).to(tr)
            if label:
                elem.label(label, loc="top")
            d += elem
            d += elm.Line().at(tr).to(right_pos)

        # ── galvanometer: horizontal through the middle ─────────────
        if "MID" in comp:
            step = comp["MID"]
            elem = self._create_element(step)
            label = self._make_label(step)
            elem.at(left_pos).to(right_pos)
            if label:
                elem.label(label, loc="bottom")
            d += elem

        # ── bottom-left arm: vertical down, wire to GND ─────────────
        if "BL" in comp:
            step = comp["BL"]
            elem = self._create_element(step)
            label = self._make_label(step)
            elem.at(left_pos).to(bl)
            if label:
                elem.label(label, loc="left")
            d += elem
            d += elm.Line().at(bl).to(bot_pos)

        # ── bottom-right arm: vertical down, wire to GND ────────────
        if "BR" in comp:
            step = comp["BR"]
            elem = self._create_element(step)
            label = self._make_label(step)
            elem.at(right_pos).to(br)
            if label:
                elem.label(label, loc="right")
            d += elem
            d += elm.Line().at(br).to(bot_pos)

        # ── any extra components (fallback positioned) ──────────────
        for step in extras:
            p1 = positions.get(step.from_node, (0.0, 0.0))
            p2 = positions.get(step.to_node, (0.0, 0.0))
            elem = self._create_element(step)
            label = self._make_label(step)
            loc = self._pick_label_loc(step.direction)
            if self._is_aligned(p1, p2):
                elem.at(p1).to(p2)
                if label:
                    elem.label(label, loc=loc)
                d += elem
            else:
                mid = self._route_intermediate(p1, p2, step.direction)
                elem.at(p1).to(mid)
                if label:
                    elem.label(label, loc=loc)
                d += elem
                d += elm.Line().at(mid).to(p2)

        # ── ground symbol ───────────────────────────────────────────
        d += elm.Ground().at(bot_pos)

        # ── junction dots ───────────────────────────────────────────
        d += elm.Dot().at(top_pos)
        d += elm.Dot().at(left_pos)
        d += elm.Dot().at(right_pos)

        return d

    # ── element factory ─────────────────────────────────────────────
    @staticmethod
    def _create_element(step: DrawStep) -> elm.Element:
        """Map a :class:`DrawStep` to the matching schemdraw element."""
        if step.comp_type == "V":
            waveform = step.extra.get("waveform", "DC")
            if waveform == "AC":
                return elm.SourceSin()
            return elm.SourceV()

        cls = _ELEMENT_MAP.get(step.comp_type, elm.Line)
        return cls()

    # ── label formatting ────────────────────────────────────────────
    @staticmethod
    def _make_label(step: DrawStep) -> str:
        """Build a human-readable label with name + SI-prefixed value."""
        name = step.comp_name
        value_str = _format_value(step.value, step.comp_type)

        # Append frequency for AC sources
        if step.comp_type == "V" and step.extra.get("waveform") == "AC":
            freq = step.extra.get("frequency")
            if freq is not None:
                if freq >= 1e6:
                    freq_str = f"{freq / 1e6:.4g} MHz"
                elif freq >= 1e3:
                    freq_str = f"{freq / 1e3:.4g} kHz"
                else:
                    freq_str = f"{freq:.4g} Hz"
                value_str = f"{value_str}, {freq_str}" if value_str else freq_str

        if value_str:
            return f"{name}\n{value_str}"
        return name

    # ── geometry helpers ────────────────────────────────────────────
    @staticmethod
    def _pick_label_loc(direction: str) -> str:
        """Choose label placement that avoids overlaps for a given
        component direction."""
        if direction == "up":
            return "right"
        if direction == "down":
            return "left"
        # horizontal ("right" / "left") → label above
        return "top"

    @staticmethod
    def _is_aligned(
        p1: tuple[float, float],
        p2: tuple[float, float],
        tol: float = 0.1,
    ) -> bool:
        """True when *p1* and *p2* share a horizontal or vertical line."""
        return abs(p1[0] - p2[0]) < tol or abs(p1[1] - p2[1]) < tol

    @staticmethod
    def _route_intermediate(
        p1: tuple[float, float],
        p2: tuple[float, float],
        direction: str,
    ) -> tuple[float, float]:
        """
        Compute the midpoint of an L-shaped route.

        The component occupies the first leg (along *direction*) and a
        straight wire covers the second leg to reach *p2*.
        """
        if direction in ("up", "down"):
            # Vertical first, then horizontal
            return (p1[0], p2[1])
        # Horizontal first, then vertical
        return (p2[0], p1[1])

    # ── output ──────────────────────────────────────────────────────
    def Summary(self) -> None:
        """Print a compact rendering plan."""
        pattern = self._layout.Pattern
        positions = self._layout.Positions
        steps = self._layout.DrawOrder

        print(f"SchematicDrawer: pattern={pattern.name}, "
              f"nodes={len(positions)}, steps={len(steps)}")
        print()

        for i, step in enumerate(steps):
            p1 = positions.get(step.from_node, (0, 0))
            p2 = positions.get(step.to_node, (0, 0))
            aligned = self._is_aligned(p1, p2)
            route = "straight" if aligned else "L-route"
            label = self._make_label(step)
            label_short = label.replace("\n", " | ")
            print(f"  {i + 1}. {step.comp_name} [{step.comp_type}] "
                  f"{step.from_node}→{step.to_node} "
                  f"({route}) {label_short}")
        print()

    def __repr__(self) -> str:
        return (f"SchematicDrawer(pattern={self._layout.Pattern.name}, "
                f"steps={len(self._layout.DrawOrder)})")
