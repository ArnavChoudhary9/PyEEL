"""
LivePlotter — real-time, non-blocking probe visualisation (matplotlib).

Groups of probes are plotted simultaneously.  Each *group* is a list of
probes that share one subplot (overlaid).  Different groups get different
subplots stacked vertically in the same figure window.

Uses :class:`CircularBuffer` internally so memory stays bounded no
matter how long the simulation runs.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from .Probe import Probe, ProbeType
from .Scope._buffer import CircularBuffer


class _PlotChannel:
    """Pairs a probe with a circular buffer and a matplotlib line."""

    __slots__ = ("probe", "buffer", "line")

    def __init__(self, probe: Probe, buffer_capacity: int) -> None:
        self.probe = probe
        self.buffer = CircularBuffer(buffer_capacity)
        self.line: Line2D | None = None

    def ingest(self) -> None:
        """Drain new samples from the probe into the circular buffer."""
        n = len(self.probe.TimeData)
        if n == 0:
            return
        t = np.array(self.probe.TimeData, dtype=np.float64)
        v = np.array(self.probe.ValueData, dtype=np.float64)
        self.buffer.push_bulk(t, v)
        self.probe.TimeData.clear()
        self.probe.ValueData.clear()


class LivePlotter:
    """
    Non-blocking, continuously-updating matplotlib figure for probes.

    Parameters
    ----------
    *groups : list[Probe]
        Each positional argument is a list of probes whose data will be
        overlaid on the **same** subplot.
    window : float | None
        If given, only the last *window* seconds are shown on the x-axis.
    update_interval : float
        Minimum seconds between actual redraws (throttle).
    buffer_capacity : int
        Per-channel circular buffer size.  Default 200 000 samples.
    """

    _channel_groups: list[list[_PlotChannel]]
    _window: float | None
    _interval: float

    _fig: Figure
    _axes: list[Axes]
    _initialized: bool

    def __init__(
        self,
        *groups: list[Probe],
        window: float | None = None,
        update_interval: float = 0.03,
        buffer_capacity: int = 200_000,
    ):
        if not groups:
            raise ValueError("LivePlotter requires at least one probe group.")

        self._window = window
        self._interval = update_interval
        self._initialized = False

        # ── wrap probes in channels ─────────────────────────────────
        self._channel_groups = []
        for group in groups:
            self._channel_groups.append(
                [_PlotChannel(p, buffer_capacity) for p in group]
            )

        # ── create figure & subplots ────────────────────────────────
        n = len(self._channel_groups)
        self._fig, axes = plt.subplots(n, 1, squeeze=False, figsize=(8, 3 * n))
        self._axes = [axes[i, 0] for i in range(n)]

        # ── create one Line2D per channel ───────────────────────────
        for ax, ch_group in zip(self._axes, self._channel_groups):
            for ch in ch_group:
                label = ch.probe._get_label()
                (line,) = ax.plot([], [], linewidth=1.0, label=label)
                ch.line = line
            ax.set_xlabel("Time (s)")
            ax.set_ylabel(self._y_label(ch_group))
            ax.legend(loc="upper right", fontsize="small")
            ax.grid(True, alpha=0.3)

        self._fig.tight_layout()
        plt.ion()
        self._fig.show()
        self._fig.canvas.flush_events()
        self._initialized = True

    # ── public API ──────────────────────────────────────────────────
    def Update(self) -> None:
        """Redraw every subplot with the latest probe data."""
        if not self._initialized or not plt.fignum_exists(self._fig.number):
            return

        for ax, ch_group in zip(self._axes, self._channel_groups):
            x_min, x_max = float("inf"), float("-inf")

            for ch in ch_group:
                ch.ingest()

                if self._window is not None:
                    t, v = ch.buffer.get_window(self._window)
                else:
                    t, v = ch.buffer.get_ordered()

                if ch.line is not None:
                    ch.line.set_data(t, v)

                if len(t) > 0:
                    x_min = min(x_min, t[0])
                    x_max = max(x_max, t[-1])

            if x_min < x_max:
                ax.set_xlim(x_min, x_max)

            ax.relim()
            ax.autoscale_view(scalex=False, scaley=True)

        self._fig.canvas.draw_idle()
        self._fig.canvas.flush_events()
        plt.pause(self._interval)

    def Close(self) -> None:
        """Close the figure window."""
        if self._initialized and plt.fignum_exists(self._fig.number):
            plt.close(self._fig)
        self._initialized = False

    def KeepOpen(self) -> None:
        """Block so the window stays open after the simulation loop."""
        if self._initialized and plt.fignum_exists(self._fig.number):
            plt.ioff()
            plt.show()

    @property
    def IsOpen(self) -> bool:
        """``True`` while the figure window is still open."""
        return self._initialized and plt.fignum_exists(self._fig.number)

    # ── helpers ─────────────────────────────────────────────────────
    @staticmethod
    def _y_label(channels: list[_PlotChannel]) -> str:
        units = set()
        for ch in channels:
            units.add("V" if ch.probe.Type == ProbeType.VOLTAGE else "A")
        parts = sorted(units)
        return " / ".join(f"({u})" for u in parts)

    def __del__(self) -> None:
        try:
            self.Close()
        except Exception:
            pass
