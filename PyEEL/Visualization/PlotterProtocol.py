"""
PlotterProtocol — structural typing interface for live visualizers.

Any class that implements ``Update()``, ``Close()``, ``KeepOpen()``,
and ``IsOpen`` (property) is a valid ``LivePlotterProtocol``.

Both :class:`LivePlotter` and :class:`Scope` satisfy this protocol,
so :class:`LiveSimulation` can accept either one interchangeably.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LivePlotterProtocol(Protocol):
    """Structural interface shared by LivePlotter and Scope."""

    def Update(self) -> None:
        """Redraw with the latest probe data."""
        ...

    def Close(self) -> None:
        """Close the visualization window."""
        ...

    def KeepOpen(self) -> None:
        """Block until the user closes the window."""
        ...

    @property
    def IsOpen(self) -> bool:
        """``True`` while the visualization window is visible."""
        ...
