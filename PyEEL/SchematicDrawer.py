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
        d = schemdraw.Drawing(unit=self._layout.Grid)

        positions = self._layout.Positions
        draw_order = self._layout.DrawOrder
        gnd = self._layout.GroundNode

        # ── components ──────────────────────────────────────────────
        for step in draw_order:
            p1 = positions.get(step.from_node, (0.0, 0.0))
            p2 = positions.get(step.to_node, (0.0, 0.0))

            element = self._create_element(step)
            label = self._make_label(step)

            if self._is_aligned(p1, p2):
                # Straight horizontal or vertical segment
                element.at(p1).to(p2)
                if label:
                    element.label(label)
                d += element
            else:
                # L-route: component along primary axis, wire for the
                # remaining perpendicular segment.
                mid = self._route_intermediate(p1, p2, step.direction)
                element.at(p1).to(mid)
                if label:
                    element.label(label)
                d += element
                d += elm.Line().at(mid).to(p2)

        # ── ground symbol ───────────────────────────────────────────
        gnd_pos = positions.get(gnd)
        if gnd_pos is not None:
            d += elm.Ground().at(gnd_pos)

        # ── junction dots (nodes touched by 3+ component legs) ──────
        touch: dict[str, int] = {}
        for step in draw_order:
            touch[step.from_node] = touch.get(step.from_node, 0) + 1
            touch[step.to_node] = touch.get(step.to_node, 0) + 1

        for node, count in touch.items():
            if count > 2 and node != gnd:
                pos = positions.get(node)
                if pos is not None:
                    d += elm.Dot().at(pos)

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
