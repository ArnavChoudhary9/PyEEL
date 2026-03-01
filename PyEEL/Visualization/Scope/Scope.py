"""
Scope — drop-in replacement for :class:`LivePlotter` with a full
oscilloscope-style UI powered by pyqtgraph / PyQt6.

Key advantages over LivePlotter
-------------------------------
* **Fixed memory** — each channel uses a :class:`CircularBuffer`, so
  memory stays constant no matter how long the simulation runs.
* **Trigger system** — edge-based triggering with Auto / Normal /
  Single / Free modes.
* **Auto-hold** — automatically snapshots and dims previous sweeps.
* **Measurements** — live Vpp, Vrms, frequency, period, duty-cycle,
  rise/fall time displayed on-screen.
* **High performance** — pyqtgraph is GPU-accelerated on most
  platforms and can comfortably handle >100 k samples at 60 fps.

Usage
-----
``Scope`` accepts the **same group syntax** as ``LivePlotter`` so it can
be swapped in with a one-line change::

    # before
    plotter = LivePlotter([v_probe], [i_probe], window=0.02)

    # after
    plotter = Scope([v_probe], [i_probe], window=0.02)

The rest of the simulation loop (``plotter.Update()``, ``plotter.Close()``,
``plotter.KeepOpen()``, ``plotter.IsOpen``) works identically.
"""

from __future__ import annotations

import sys
import time
from typing import Optional

import numpy as np

from PyQt6 import QtWidgets

from ..Probe import Probe, ProbeType

from ._buffer import CircularBuffer
from ._channel import ScopeChannel
from ._trigger import Trigger, TriggerEdge, TriggerMode, TriggerState
from ._measurements import compute_measurements, MeasurementResult
from ._renderer import ScopeRenderer


# Ensure there's a running QApplication
_qapp: Optional[QtWidgets.QApplication] = None


def _ensure_qapp() -> QtWidgets.QApplication:
    global _qapp
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
        _qapp = app
    return app  # type: ignore[return-value]


class Scope:
    """
    Oscilloscope-style live visualization for PyEEL probes.

    Parameters
    ----------
    *groups : list[Probe]
        Each positional argument is a list of probes whose waveforms
        are overlaid.  All groups share one plot pane (like a real
        scope — one screen, many channels).
    window : float
        Time-window width in seconds (default 20 ms).
    buffer_capacity : int
        Per-channel ring-buffer size.  Determines how much history is
        kept.  Default 200 000 samples → ~1-2 MB per channel.
    update_interval : float
        Minimum real-time seconds between redraws (throttle).
    trigger_level : float
        Initial trigger level.
    trigger_edge : TriggerEdge
        Initial trigger edge.
    trigger_mode : TriggerMode
        Initial trigger mode.
    trigger_source : int
        Index of the channel used as trigger source (0-based, across
        all groups, flattened).
    show_measurements : bool
        Whether to display the measurement HUD on start.
    title : str
        Window title.
    """

    _channels: list[ScopeChannel]
    _trigger: Trigger
    _renderer: ScopeRenderer
    _app: QtWidgets.QApplication
    _interval: float
    _last_render: float
    _closed: bool

    def __init__(
        self,
        *groups: list[Probe],
        window: float = 0.02,
        buffer_capacity: int = 200_000,
        update_interval: float = 0.016,       # ~60 fps
        trigger_level: float = 0.0,
        trigger_edge: TriggerEdge = TriggerEdge.RISING,
        trigger_mode: TriggerMode = TriggerMode.AUTO,
        trigger_source: int = 0,
        show_measurements: bool = True,
        title: str = "PyEEL Scope",
    ) -> None:
        if not groups:
            raise ValueError("Scope requires at least one probe group.")

        self._app = _ensure_qapp()
        self._interval = update_interval
        self._last_render = 0.0
        self._closed = False

        # ── flatten groups into channels ────────────────────────────
        self._channels = []
        idx = 0
        for group in groups:
            for probe in group:
                ch = ScopeChannel(
                    probe, index=idx, buffer_capacity=buffer_capacity,
                )
                self._channels.append(ch)
                idx += 1

        # ── trigger ─────────────────────────────────────────────────
        source_ch = (
            self._channels[trigger_source]
            if 0 <= trigger_source < len(self._channels)
            else self._channels[0]
        )
        self._trigger = Trigger(
            source=source_ch,
            level=trigger_level,
            edge=trigger_edge,
            mode=trigger_mode,
        )

        # ── renderer (the Qt window) ───────────────────────────────
        self._renderer = ScopeRenderer(
            channels=self._channels,
            trigger=self._trigger,
            title=title,
            window=window,
            show_measurements=show_measurements,
        )
        self._renderer.closed.connect(self._on_closed)
        self._renderer.show()

        # pump events so the window actually appears
        self._app.processEvents()

    # ================================================================
    # Public API — compatible with LivePlotter
    # ================================================================

    def Update(self) -> None:
        """
        Ingest new probe data and redraw.  Call this from the
        simulation loop, exactly like ``LivePlotter.Update()``.
        """
        if self._closed:
            return

        now = time.perf_counter()
        dt = now - self._last_render if self._last_render else 0.016

        # 1. ingest data from probes into circular buffers
        for ch in self._channels:
            ch.ingest()

        # 2. trigger processing
        current_time = 0.0
        for ch in self._channels:
            lt = ch.buffer.latest_time
            if lt is not None and lt > current_time:
                current_time = lt

        triggered = self._trigger.process(current_time, dt)

        # 3. throttle rendering
        if (now - self._last_render) < self._interval:
            self._app.processEvents()
            return

        self._last_render = now

        # 4. render
        self._renderer.draw_frame(dt)
        self._trigger.acknowledge()

        # 5. process Qt events
        self._app.processEvents()

    def Close(self) -> None:
        """Close the scope window."""
        if not self._closed:
            self._renderer.close()
            self._closed = True

    def KeepOpen(self) -> None:
        """
        Block until the user closes the scope window.  Equivalent to
        ``LivePlotter.KeepOpen()``.
        """
        if self._closed:
            return
        # enter the Qt event loop
        while self._renderer.is_open:
            self._app.processEvents()
            time.sleep(0.01)

    @property
    def IsOpen(self) -> bool:
        """``True`` while the scope window is visible."""
        return not self._closed and self._renderer.is_open

    # ================================================================
    # Extended API (beyond LivePlotter)
    # ================================================================

    @property
    def channels(self) -> list[ScopeChannel]:
        return list(self._channels)

    @property
    def trigger(self) -> Trigger:
        return self._trigger

    @property
    def renderer(self) -> ScopeRenderer:
        return self._renderer

    def get_measurements(self, channel_index: int = 0) -> MeasurementResult:
        """Compute measurements for a specific channel right now."""
        ch = self._channels[channel_index]
        t, v = ch.get_display_data(window=self._renderer._time_window)
        return compute_measurements(t, v)

    def set_time_window(self, seconds: float) -> None:
        """Programmatically change the time window."""
        self._renderer._time_window = seconds

    def clear_all(self) -> None:
        """Clear all channel buffers and held waveforms."""
        for ch in self._channels:
            ch.clear()
        self._renderer._clear_holds()

    # ================================================================
    # Internal
    # ================================================================

    def _on_closed(self) -> None:
        self._closed = True

    def __del__(self) -> None:
        try:
            self.Close()
        except Exception:
            pass
