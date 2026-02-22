"""
LivePlotter — real-time, non-blocking probe visualisation.

Groups of probes are plotted simultaneously.  Each *group* is a list of
probes that share one subplot (overlaid).  Different groups get different
subplots stacked vertically in the same figure window.
"""

from __future__ import annotations

import bisect
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from .Probe import Probe, ProbeType


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
    """

    _groups: list[list[Probe]]
    _window: float | None
    _interval: float

    _fig: Figure
    _axes: list[Axes]
    _lines: list[list[Line2D]]
    _initialized: bool

    def __init__(self, *groups: list[Probe],
                 window: float | None = None,
                 update_interval: float = 0.03):
        if not groups:
            raise ValueError("LivePlotter requires at least one probe group.")

        self._groups = list(groups)
        self._window = window
        self._interval = update_interval
        self._initialized = False

        # ── create figure & subplots ────────────────────────────────
        n = len(self._groups)
        self._fig, axes = plt.subplots(n, 1, squeeze=False, figsize=(8, 3 * n))
        self._axes = [axes[i, 0] for i in range(n)]

        # ── create one Line2D per probe ─────────────────────────────
        self._lines = []
        for ax, group in zip(self._axes, self._groups):
            group_lines: list[Line2D] = []
            for probe in group:
                label = probe._get_label()
                (line,) = ax.plot([], [], linewidth=1.0, label=label)
                group_lines.append(line)
            ax.set_xlabel("Time (s)")
            ax.set_ylabel(self._y_label(group))
            ax.legend(loc="upper right", fontsize="small")
            ax.grid(True, alpha=0.3)
            self._lines.append(group_lines)

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

        for ax, group, lines in zip(self._axes, self._groups, self._lines):
            x_min, x_max = float("inf"), float("-inf")

            for probe, line in zip(group, lines):
                if self._window is not None and len(probe.TimeData) > 0:
                    t_max = probe.TimeData[-1]
                    t_min = t_max - self._window
                    idx = bisect.bisect_left(probe.TimeData, t_min)
                    t = np.array(probe.TimeData[idx:])
                    v = np.array(probe.ValueData[idx:])
                else:
                    t = np.array(probe.TimeData)
                    v = np.array(probe.ValueData)

                line.set_data(t, v)

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
        """
        Switch to blocking mode so the window stays open after the
        simulation loop ends.
        """
        if self._initialized and plt.fignum_exists(self._fig.number):
            plt.ioff()
            plt.show()

    @property
    def IsOpen(self) -> bool:
        """``True`` while the figure window is still open."""
        return self._initialized and plt.fignum_exists(self._fig.number)

    # ── helpers ─────────────────────────────────────────────────────
    @staticmethod
    def _y_label(group: list[Probe]) -> str:
        units = set()
        for p in group:
            units.add("V" if p.Type == ProbeType.VOLTAGE else "A")
        parts = sorted(units)
        return " / ".join(f"({u})" for u in parts)

    def __del__(self):
        try:
            self.Close()
        except Exception:
            pass
