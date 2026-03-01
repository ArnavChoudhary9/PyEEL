"""
_buffer — Fixed-capacity circular (ring) buffer backed by NumPy arrays.

This is the **core fix** for the memory-leak issue: instead of appending to
ever-growing Python lists, data is stored in pre-allocated NumPy arrays of
a fixed capacity.  When the buffer is full the oldest samples are silently
overwritten, keeping memory usage constant regardless of simulation length.
"""

from __future__ import annotations

import numpy as np


class CircularBuffer:
    """
    A fast, fixed-capacity ring buffer for ``(time, value)`` pairs.

    Parameters
    ----------
    capacity : int
        Maximum number of samples the buffer can hold.  Once full, the
        oldest sample is overwritten on each new :meth:`push`.
    """

    __slots__ = ("_cap", "_t", "_v", "_head", "_count")

    _cap: int
    _t: np.ndarray          # float64[capacity]
    _v: np.ndarray          # float64[capacity]
    _head: int              # next write position
    _count: int             # total samples written (may exceed _cap)

    def __init__(self, capacity: int = 100_000) -> None:
        if capacity < 1:
            raise ValueError("Capacity must be >= 1.")
        self._cap = capacity
        self._t = np.empty(capacity, dtype=np.float64)
        self._v = np.empty(capacity, dtype=np.float64)
        self._head = 0
        self._count = 0

    # ── write ───────────────────────────────────────────────────────
    def push(self, time: float, value: float) -> None:
        """Append one sample, overwriting the oldest if full."""
        self._t[self._head] = time
        self._v[self._head] = value
        self._head = (self._head + 1) % self._cap
        self._count += 1

    def push_bulk(self, times: np.ndarray, values: np.ndarray) -> None:
        """Append multiple samples efficiently."""
        n = len(times)
        if n == 0:
            return

        if n >= self._cap:
            # More data than capacity — keep only the newest _cap samples
            self._t[:] = times[-self._cap:]
            self._v[:] = values[-self._cap:]
            self._head = 0
            self._count += n
            return

        end = self._head + n
        if end <= self._cap:
            self._t[self._head:end] = times
            self._v[self._head:end] = values
        else:
            first = self._cap - self._head
            self._t[self._head:] = times[:first]
            self._v[self._head:] = values[:first]
            rest = n - first
            self._t[:rest] = times[first:]
            self._v[:rest] = values[first:]

        self._head = end % self._cap
        self._count += n

    # ── read (zero-copy views when possible) ────────────────────────
    def get_ordered(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Return ``(times, values)`` in chronological order.

        If the buffer has never wrapped, this is a simple slice —
        **zero-copy**.  After wrapping, a concatenation is needed (still
        very fast for typical scope sizes).
        """
        size = self.size
        if size == 0:
            return np.empty(0), np.empty(0)

        if size < self._cap:
            # Haven't wrapped yet — contiguous
            return self._t[:size], self._v[:size]

        # Wrapped — stitch tail + head portions
        return (
            np.concatenate((self._t[self._head:], self._t[:self._head])),
            np.concatenate((self._v[self._head:], self._v[:self._head])),
        )

    def get_window(self, window: float) -> tuple[np.ndarray, np.ndarray]:
        """
        Return only the most-recent *window* seconds of data,
        in chronological order.
        """
        t, v = self.get_ordered()
        if len(t) == 0:
            return t, v
        t_min = t[-1] - window
        mask = t >= t_min
        return t[mask], v[mask]

    # ── metadata ────────────────────────────────────────────────────
    @property
    def size(self) -> int:
        """Number of valid samples currently held."""
        return min(self._count, self._cap)

    @property
    def capacity(self) -> int:
        return self._cap

    @property
    def is_full(self) -> bool:
        return self._count >= self._cap

    @property
    def latest_time(self) -> float | None:
        if self._count == 0:
            return None
        idx = (self._head - 1) % self._cap
        return float(self._t[idx])

    @property
    def latest_value(self) -> float | None:
        if self._count == 0:
            return None
        idx = (self._head - 1) % self._cap
        return float(self._v[idx])

    # ── housekeeping ────────────────────────────────────────────────
    def clear(self) -> None:
        """Reset the buffer without reallocating memory."""
        self._head = 0
        self._count = 0

    def resize(self, new_capacity: int) -> None:
        """
        Change capacity, preserving as many recent samples as possible.

        This *does* allocate new arrays.
        """
        if new_capacity < 1:
            raise ValueError("Capacity must be >= 1.")
        t, v = self.get_ordered()
        keep = min(len(t), new_capacity)
        self._cap = new_capacity
        self._t = np.empty(new_capacity, dtype=np.float64)
        self._v = np.empty(new_capacity, dtype=np.float64)
        self._t[:keep] = t[-keep:]
        self._v[:keep] = v[-keep:]
        self._head = keep % new_capacity
        self._count = keep

    def __len__(self) -> int:
        return self.size

    def __repr__(self) -> str:
        return (
            f"CircularBuffer(capacity={self._cap}, "
            f"size={self.size}, full={self.is_full})"
        )
