"""
_channel — ScopeChannel wraps a Probe with a CircularBuffer and display
configuration (colour, scale, offset, visibility).

Each channel owns its own fixed-capacity buffer so we never grow
unbounded memory.  The channel also holds references to the pyqtgraph
curve items so the renderer can toggle / recolour them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from ._buffer import CircularBuffer

if TYPE_CHECKING:
    from ..Probe import Probe


# Default scope colours — classic Tektronix / Rigol palette
_DEFAULT_COLOURS: list[str] = [
    "#FFFF00",  # CH1 — yellow
    "#00FFFF",  # CH2 — cyan
    "#FF00FF",  # CH3 — magenta
    "#00FF00",  # CH4 — green
    "#FF8800",  # CH5 — orange
    "#FF4444",  # CH6 — red
    "#44AAFF",  # CH7 — blue
    "#AAAAAA",  # CH8 — grey
]


class ScopeChannel:
    """
    One scope channel — binds a :class:`Probe` to a circular buffer and
    display configuration.

    Parameters
    ----------
    probe : Probe
        The measurement probe this channel reads from.
    index : int
        Channel number (0-based), used for default colour selection.
    buffer_capacity : int
        Maximum samples in the rolling buffer.
    colour : str | None
        Override colour (hex string).  ``None`` → automatic.
    label : str | None
        Override label.  ``None`` → probe's label.
    """

    __slots__ = (
        "_probe", "_index", "_buffer", "_colour", "_label",
        "_visible", "_v_scale", "_v_offset",
        "_curve_item",      # set by the renderer
        "_hold_curves",     # list of held waveform curve items
    )

    def __init__(
        self,
        probe: Probe,
        index: int = 0,
        buffer_capacity: int = 200_000,
        colour: str | None = None,
        label: str | None = None,
    ) -> None:
        self._probe = probe
        self._index = index
        self._buffer = CircularBuffer(buffer_capacity)
        self._colour = colour or _DEFAULT_COLOURS[index % len(_DEFAULT_COLOURS)]
        self._label = label or probe._get_label()
        self._visible = True
        self._v_scale = 1.0      # volts-per-division multiplier
        self._v_offset = 0.0     # vertical offset (in signal units)
        self._curve_item = None
        self._hold_curves: list = []

    # ── properties ──────────────────────────────────────────────────
    @property
    def probe(self) -> Probe:
        return self._probe

    @property
    def index(self) -> int:
        return self._index

    @property
    def buffer(self) -> CircularBuffer:
        return self._buffer

    @property
    def colour(self) -> str:
        return self._colour

    @colour.setter
    def colour(self, value: str) -> None:
        self._colour = value
        if self._curve_item is not None:
            self._curve_item.setPen(value, width=1.5)

    @property
    def label(self) -> str:
        return self._label

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value
        if self._curve_item is not None:
            self._curve_item.setVisible(value)

    @property
    def v_scale(self) -> float:
        return self._v_scale

    @v_scale.setter
    def v_scale(self, value: float) -> None:
        self._v_scale = max(1e-12, value)

    @property
    def v_offset(self) -> float:
        return self._v_offset

    @v_offset.setter
    def v_offset(self, value: float) -> None:
        self._v_offset = value

    @property
    def unit(self) -> str:
        from ..Probe import ProbeType
        return "V" if self._probe.Type == ProbeType.VOLTAGE else "A"

    # ── data flow ───────────────────────────────────────────────────
    def ingest(self) -> int:
        """
        Pull *new* data from the probe's lists into the circular buffer,
        then **clear** the probe's lists to prevent the original leak.

        Returns the number of new samples ingested.
        """
        probe = self._probe
        n_probe = len(probe.TimeData)
        if n_probe == 0:
            return 0

        t = np.array(probe.TimeData, dtype=np.float64)
        v = np.array(probe.ValueData, dtype=np.float64)

        self._buffer.push_bulk(t, v)

        # Clear the probe lists so they don't grow without bound.
        probe.TimeData.clear()
        probe.ValueData.clear()

        return n_probe

    def get_display_data(
        self, window: float | None = None
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Return ``(t, v)`` suitable for plotting, applying vertical
        scale and offset.
        """
        if window is not None:
            t, v = self._buffer.get_window(window)
        else:
            t, v = self._buffer.get_ordered()
        if len(v) > 0:
            v = (v + self._v_offset) * self._v_scale
        return t, v

    def clear(self) -> None:
        """Clear both the buffer and the probe's lists."""
        self._buffer.clear()
        self._probe.TimeData.clear()
        self._probe.ValueData.clear()

    def __repr__(self) -> str:
        return f"ScopeChannel(CH{self._index + 1}, {self._label})"
