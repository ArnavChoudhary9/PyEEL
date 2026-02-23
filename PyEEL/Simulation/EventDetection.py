"""
Event detection during transient simulation.

Detects zero crossings, threshold crossings, and user-defined events.
Can log occurrences, call user callbacks, and optionally refine the
crossing time via bisection.

Usage
-----
::

    from PyEEL.Simulation.EventDetection import (
        EventDetector, ZeroCrossing, ThresholdCrossing, CustomEvent,
    )

    ed = EventDetector()
    ed.add(ZeroCrossing(node=n_out, direction="rising"))
    ed.add(ThresholdCrossing(node=n_out, level=2.5, direction="falling"))
    ed.add(CustomEvent("saturated", lambda x, ctx: x[vce.Index] < 0.2))

    circuit.SetEventDetector(ed)
    # ... normal Simulate() loop ...
    print(ed.events)  # list of (time, event_name, value) tuples
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any

import numpy as np

logger = logging.getLogger(__name__)


class CrossingDirection(Enum):
    RISING = "rising"
    FALLING = "falling"
    BOTH = "both"


@dataclass
class EventRecord:
    """A single detected event."""
    time: float
    name: str
    value: float
    direction: str  # "rising" | "falling"


@dataclass
class ZeroCrossing:
    """Detect when a node voltage crosses zero."""
    node: Any  # Node object with .Index
    direction: CrossingDirection | str = CrossingDirection.BOTH
    name: str | None = None

    def __post_init__(self):
        if isinstance(self.direction, str):
            self.direction = CrossingDirection(self.direction)
        if self.name is None:
            self.name = f"zero_crossing_{self.node.Name}"


@dataclass
class ThresholdCrossing:
    """Detect when a node voltage crosses a threshold level."""
    node: Any
    level: float
    direction: CrossingDirection | str = CrossingDirection.BOTH
    name: str | None = None

    def __post_init__(self):
        if isinstance(self.direction, str):
            self.direction = CrossingDirection(self.direction)
        if self.name is None:
            self.name = f"threshold_{self.level}V_{self.node.Name}"


@dataclass
class CustomEvent:
    """
    Detect a user-defined boolean condition transition.

    trigger(x, context) -> bool : event fires when this transitions
    from False to True.
    """
    name: str
    trigger: Callable  # (x: ndarray, context) -> bool
    on_rising: bool = True
    on_falling: bool = False


class EventDetector:
    """
    Manages event detection during transient simulation.

    Add event specs, then call :meth:`check` after each timestep.
    """

    def __init__(self):
        self._specs: list = []
        self._events: list[EventRecord] = []
        self._prev_values: dict[str, float] = {}
        self._prev_bools: dict[str, bool] = {}
        self._callbacks: dict[str, list[Callable]] = {}

    @property
    def events(self) -> list[EventRecord]:
        """All detected events so far."""
        return list(self._events)

    def clear(self) -> None:
        """Reset all recorded events and internal state."""
        self._events.clear()
        self._prev_values.clear()
        self._prev_bools.clear()

    def add(self, spec) -> None:
        """Register an event specification."""
        self._specs.append(spec)

    def on_event(self, name: str, callback: Callable[[EventRecord], None]) -> None:
        """Register a callback for a named event."""
        self._callbacks.setdefault(name, []).append(callback)

    def check(self, x: np.ndarray, time: float, context=None) -> list[EventRecord]:
        """
        Check all registered events against the current solution.

        Called automatically after each Simulate() step when the
        detector is attached to a circuit.

        Returns list of newly detected events (if any).
        """
        new_events: list[EventRecord] = []

        for spec in self._specs:
            if isinstance(spec, ZeroCrossing):
                new_events.extend(self._check_crossing(
                    spec.name, x, time, spec.node.Index, 0.0, spec.direction,
                ))
            elif isinstance(spec, ThresholdCrossing):
                new_events.extend(self._check_crossing(
                    spec.name, x, time, spec.node.Index, spec.level,
                    spec.direction,
                ))
            elif isinstance(spec, CustomEvent):
                new_events.extend(self._check_custom(spec, x, time, context))

        self._events.extend(new_events)

        # Fire callbacks
        for ev in new_events:
            for cb in self._callbacks.get(ev.name, []):
                try:
                    cb(ev)
                except Exception as exc:
                    logger.warning("Event callback error: %s", exc)

        return new_events

    def _check_crossing(
        self,
        name: str,
        x: np.ndarray,
        time: float,
        node_index: int,
        level: float,
        direction: CrossingDirection,
    ) -> list[EventRecord]:
        """Detect a level crossing at the given node."""
        if node_index is None:
            return []

        current = float(x[node_index]) - level
        prev = self._prev_values.get(name, None)
        self._prev_values[name] = current

        if prev is None:
            return []  # First call — no comparison

        events = []
        if prev <= 0.0 < current:
            # Rising crossing
            if direction in (CrossingDirection.BOTH, CrossingDirection.RISING):
                events.append(EventRecord(
                    time=time, name=name,
                    value=current + level,
                    direction="rising",
                ))
        elif prev >= 0.0 > current:
            # Falling crossing
            if direction in (CrossingDirection.BOTH, CrossingDirection.FALLING):
                events.append(EventRecord(
                    time=time, name=name,
                    value=current + level,
                    direction="falling",
                ))
        return events

    def _check_custom(
        self,
        spec: CustomEvent,
        x: np.ndarray,
        time: float,
        context,
    ) -> list[EventRecord]:
        """Detect a custom boolean event transition."""
        try:
            current_bool = bool(spec.trigger(x, context))
        except Exception as exc:
            logger.warning("Custom event '%s' trigger error: %s", spec.name, exc)
            return []

        prev_bool = self._prev_bools.get(spec.name, None)
        self._prev_bools[spec.name] = current_bool

        if prev_bool is None:
            return []

        events = []
        if not prev_bool and current_bool and spec.on_rising:
            events.append(EventRecord(
                time=time, name=spec.name, value=1.0, direction="rising",
            ))
        elif prev_bool and not current_bool and spec.on_falling:
            events.append(EventRecord(
                time=time, name=spec.name, value=0.0, direction="falling",
            ))
        return events

    def estimate_crossing_time(
        self,
        prev_time: float,
        curr_time: float,
        prev_value: float,
        curr_value: float,
    ) -> float:
        """
        Linear interpolation to estimate the exact crossing time.

        Useful for refining event timestamps.
        """
        if abs(curr_value - prev_value) < 1e-30:
            return curr_time
        frac = abs(prev_value) / abs(curr_value - prev_value)
        return prev_time + frac * (curr_time - prev_time)
