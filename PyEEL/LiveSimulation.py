"""
LiveSimulation — run a transient simulation with live plotting.

Wraps the simulate-then-plot loop into a single callable object with
built-in **pause / resume** support (press ``Space`` on the plot window
or call :meth:`Pause` / :meth:`Resume` programmatically).

Usage
-----
::

    sim = LiveSimulation(ckt, plotter, dt=0.0005, speed=60)
    sim.Run()          # blocks until the plot window is closed

Parameters
----------
circuit : Circuit
    A finalized circuit ready for simulation.
plotter : LivePlotter
    The live-plotting window that will be updated.
dt : float
    Time-step size in seconds.
speed : int
    Number of simulation steps computed between each visual frame.
    Higher values → faster simulation, choppier animation.
    Default ``60`` ≈ real-time at 30 fps.
"""

from __future__ import annotations

from .Circuit import Circuit
from .LivePlotter import LivePlotter


class LiveSimulation:
    """
    Manages the transient simulation loop, coupling a :class:`Circuit`
    with a :class:`LivePlotter` and providing pause/resume control.

    Pause/resume can be triggered in two ways:

    * **Keyboard** — press ``Space`` while the plot window is focused.
    * **API** — call :meth:`Pause` and :meth:`Resume`.
    """

    _circuit: Circuit
    _plotter: LivePlotter
    _dt: float
    _speed: int
    _paused: bool

    def __init__(self, circuit: Circuit, plotter: LivePlotter, *,
                 dt: float = 0.0005, speed: int = 60):
        if not circuit._Finalized:
            raise RuntimeError("Circuit must be finalized before simulation.")

        self._circuit = circuit
        self._plotter = plotter
        self._dt = dt
        self._speed = speed
        self._paused = False
        self._pause_text = None

        # ── connect Space key to toggle pause ───────────────────────
        self._plotter._fig.canvas.mpl_connect(
            "key_press_event", self._on_key_press
        )

    # ── public API ──────────────────────────────────────────────────
    def Run(self) -> None:
        """
        Start the simulation loop.  Blocks until the user closes the
        plot window.
        """
        while self._plotter.IsOpen:
            if not self._paused:
                for _ in range(self._speed):
                    self._circuit.Simulate(self._dt)
            self._plotter.Update()

        print("Plot window closed — simulation stopped.")

    def Pause(self) -> None:
        """Pause the simulation (plotting continues to stay responsive)."""
        if not self._paused:
            self._paused = True
            self._show_pause_indicator()

    def Resume(self) -> None:
        """Resume a paused simulation."""
        if self._paused:
            self._paused = False
            self._hide_pause_indicator()

    def TogglePause(self) -> None:
        """Toggle between paused and running states."""
        if self._paused:
            self.Resume()
        else:
            self.Pause()

    # ── properties ──────────────────────────────────────────────────
    @property
    def IsPaused(self) -> bool:
        """``True`` while the simulation is paused."""
        return self._paused

    @property
    def dt(self) -> float:
        """Current time-step size."""
        return self._dt

    @dt.setter
    def dt(self, value: float) -> None:
        if value <= 0:
            raise ValueError("dt must be positive.")
        self._dt = value

    @property
    def Speed(self) -> int:
        """Simulation steps computed per visual frame."""
        return self._speed

    @Speed.setter
    def Speed(self, value: int) -> None:
        if value < 1:
            raise ValueError("Speed must be at least 1.")
        self._speed = value

    # ── internal ────────────────────────────────────────────────────
    def _on_key_press(self, event) -> None:
        """Handle keyboard events on the plot window."""
        if event.key == " ":
            self.TogglePause()

    def _show_pause_indicator(self) -> None:
        """Overlay a 'PAUSED' label on the first subplot."""
        if self._pause_text is not None:
            return
        ax = self._plotter._axes[0]
        self._pause_text = ax.text(
            0.5, 0.5, "PAUSED  (Space to resume)",
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=16, fontweight="bold",
            color="white",
            bbox=dict(boxstyle="round,pad=0.5",
                      facecolor="crimson", alpha=0.85),
            zorder=100,
        )

    def _hide_pause_indicator(self) -> None:
        """Remove the 'PAUSED' overlay."""
        if self._pause_text is not None:
            self._pause_text.remove()
            self._pause_text = None
