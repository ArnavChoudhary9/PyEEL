"""
_trigger — Trigger subsystem for the oscilloscope.

Supports edge-based triggering (rising / falling / either) with
configurable level, holdoff, and operating modes:

* **Auto**   — always sweeps, but tries to synchronise on the trigger.
* **Normal** — only sweeps when a trigger event is detected.
* **Single** — arms once, captures one triggered sweep, then stops.
* **Free**   — no triggering, continuous sweep (equivalent to Auto
  with no trigger condition).
"""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ._channel import ScopeChannel


# ────────────────────────────────────────────────────────────────────
# Enums
# ────────────────────────────────────────────────────────────────────

class TriggerEdge(Enum):
    RISING = auto()
    FALLING = auto()
    EITHER = auto()


class TriggerMode(Enum):
    AUTO = auto()
    NORMAL = auto()
    SINGLE = auto()
    FREE = auto()


class TriggerState(Enum):
    """Internal state-machine states."""
    ARMED = auto()          # waiting for trigger
    TRIGGERED = auto()      # trigger detected — acquiring post-trigger
    STOPPED = auto()        # single-shot done, waiting for re-arm
    FREE_RUNNING = auto()   # no trigger logic


# ────────────────────────────────────────────────────────────────────
# Trigger
# ────────────────────────────────────────────────────────────────────

class Trigger:
    """
    Edge-trigger engine.

    Parameters
    ----------
    source : ScopeChannel | None
        The channel whose data is checked for trigger events.
        ``None`` → free-running.
    level : float
        Voltage level for edge detection.
    edge : TriggerEdge
        Which edge to trigger on.
    mode : TriggerMode
        Operating mode.
    holdoff : float
        Minimum time (s) between successive triggers.
    pre_trigger : float
        Fraction of the sweep window *before* the trigger point (0–1).
    """

    __slots__ = (
        "_source", "_level", "_edge", "_mode", "_holdoff",
        "_pre_trigger", "_state",
        "_last_trigger_time", "_prev_sample",
        "_auto_timeout", "_auto_timer",
    )

    def __init__(
        self,
        source: ScopeChannel | None = None,
        level: float = 0.0,
        edge: TriggerEdge = TriggerEdge.RISING,
        mode: TriggerMode = TriggerMode.AUTO,
        holdoff: float = 0.0,
        pre_trigger: float = 0.1,
    ) -> None:
        self._source = source
        self._level = level
        self._edge = edge
        self._mode = mode
        self._holdoff = holdoff
        self._pre_trigger = max(0.0, min(1.0, pre_trigger))

        self._state: TriggerState = (
            TriggerState.FREE_RUNNING if mode == TriggerMode.FREE
            else TriggerState.ARMED
        )
        self._last_trigger_time: float = -1e30
        self._prev_sample: float | None = None

        # auto-trigger timeout: if no edge within this many seconds,
        # force a sweep anyway
        self._auto_timeout: float = 0.1  # 100 ms default
        self._auto_timer: float = 0.0

    # ── properties ──────────────────────────────────────────────────
    @property
    def source(self) -> ScopeChannel | None:
        return self._source

    @source.setter
    def source(self, ch: ScopeChannel | None) -> None:
        self._source = ch
        self._prev_sample = None

    @property
    def level(self) -> float:
        return self._level

    @level.setter
    def level(self, value: float) -> None:
        self._level = value

    @property
    def edge(self) -> TriggerEdge:
        return self._edge

    @edge.setter
    def edge(self, value: TriggerEdge) -> None:
        self._edge = value

    @property
    def mode(self) -> TriggerMode:
        return self._mode

    @mode.setter
    def mode(self, value: TriggerMode) -> None:
        self._mode = value
        if value == TriggerMode.FREE:
            self._state = TriggerState.FREE_RUNNING
        elif self._state in (TriggerState.FREE_RUNNING, TriggerState.STOPPED):
            self._state = TriggerState.ARMED

    @property
    def state(self) -> TriggerState:
        return self._state

    @property
    def pre_trigger(self) -> float:
        return self._pre_trigger

    @pre_trigger.setter
    def pre_trigger(self, value: float) -> None:
        self._pre_trigger = max(0.0, min(1.0, value))

    # ── control ─────────────────────────────────────────────────────
    def arm(self) -> None:
        """Re-arm the trigger (used after Single shot stops)."""
        self._state = TriggerState.ARMED
        self._prev_sample = None
        self._auto_timer = 0.0

    def force(self) -> None:
        """Force an immediate trigger event."""
        self._state = TriggerState.TRIGGERED

    # ── main logic ──────────────────────────────────────────────────
    def process(self, current_time: float, dt: float) -> bool:
        """
        Called once per display frame.  Returns ``True`` when a new
        sweep should be shown (trigger fired or auto-timeout).
        """
        if self._state == TriggerState.FREE_RUNNING:
            return True  # always sweep

        if self._state == TriggerState.STOPPED:
            return False  # waiting for explicit re-arm

        # ── accumulate auto-timer ───────────────────────────────────
        self._auto_timer += dt

        # ── check for edge on source channel ────────────────────────
        if self._source is not None and self._state == TriggerState.ARMED:
            latest = self._source.buffer.latest_value
            if latest is not None:
                if self._prev_sample is not None:
                    if self._detect_edge(self._prev_sample, latest):
                        if (current_time - self._last_trigger_time) >= self._holdoff:
                            self._last_trigger_time = current_time
                            self._auto_timer = 0.0
                            self._state = TriggerState.TRIGGERED
                            return True
                self._prev_sample = latest

        # ── auto-timeout (only in AUTO mode) ────────────────────────
        if self._mode == TriggerMode.AUTO and self._auto_timer >= self._auto_timeout:
            self._auto_timer = 0.0
            return True

        return False

    def acknowledge(self) -> None:
        """
        Called after a triggered sweep has been rendered.  Transitions
        the state machine according to mode.
        """
        if self._state != TriggerState.TRIGGERED:
            return
        if self._mode == TriggerMode.SINGLE:
            self._state = TriggerState.STOPPED
        else:
            self._state = TriggerState.ARMED
            self._prev_sample = None
            self._auto_timer = 0.0

    # ── edge detection ──────────────────────────────────────────────
    def _detect_edge(self, prev: float, curr: float) -> bool:
        if self._edge == TriggerEdge.RISING:
            return prev < self._level <= curr
        elif self._edge == TriggerEdge.FALLING:
            return prev > self._level >= curr
        else:  # EITHER
            return (prev < self._level <= curr) or (prev > self._level >= curr)
