"""
_measurements — Real-time waveform measurement engine.

Computes common oscilloscope measurements from the visible slice of a
channel's circular buffer:

* **Vpp**        — peak-to-peak voltage
* **Vmax / Vmin** — absolute maximum / minimum
* **Vmean**      — arithmetic mean
* **Vrms**       — root-mean-square
* **Frequency**  — dominant frequency via zero-crossing or FFT
* **Period**     — 1 / frequency
* **Duty cycle** — fraction of period above the mid-level
* **Rise time**  — 10 → 90 % transition time
* **Fall time**  — 90 → 10 % transition time

All routines are *stateless* — they operate on whatever numpy arrays you
pass in, making them easy to unit-test in isolation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass(slots=True)
class MeasurementResult:
    """Container for a full set of measurements on one waveform."""
    vpp: float = 0.0
    vmax: float = 0.0
    vmin: float = 0.0
    vmean: float = 0.0
    vrms: float = 0.0
    frequency: Optional[float] = None
    period: Optional[float] = None
    duty_cycle: Optional[float] = None
    rise_time: Optional[float] = None
    fall_time: Optional[float] = None
    pos_width: Optional[float] = None
    neg_width: Optional[float] = None

    def summary_text(self, unit: str = "V") -> str:
        """One-liner for the HUD overlay."""
        parts: list[str] = [
            f"Vpp={_fmt(self.vpp, unit)}",
            f"Vmax={_fmt(self.vmax, unit)}",
            f"Vmin={_fmt(self.vmin, unit)}",
            f"Vmean={_fmt(self.vmean, unit)}",
            f"Vrms={_fmt(self.vrms, unit)}",
        ]
        if self.frequency is not None:
            parts.append(f"f={_fmt_freq(self.frequency)}")
        if self.period is not None:
            parts.append(f"T={_fmt_time(self.period)}")
        if self.duty_cycle is not None:
            parts.append(f"Duty={self.duty_cycle:.1%}")
        if self.rise_time is not None:
            parts.append(f"Trise={_fmt_time(self.rise_time)}")
        if self.fall_time is not None:
            parts.append(f"Tfall={_fmt_time(self.fall_time)}")
        return "  |  ".join(parts)


# ── public API ──────────────────────────────────────────────────────

def compute_measurements(
    t: np.ndarray,
    v: np.ndarray,
    *,
    freq_method: str = "zero_crossing",  # or "fft"
) -> MeasurementResult:
    """
    Compute all measurements from chronologically-ordered arrays.

    Parameters
    ----------
    t, v : array-like
        Time and value arrays (same length, monotonic *t*).
    freq_method : str
        ``"zero_crossing"`` (fast) or ``"fft"`` (more robust for noisy signals).
    """
    if len(t) < 2:
        return MeasurementResult()

    v = np.asarray(v, dtype=np.float64)
    t = np.asarray(t, dtype=np.float64)

    vmax = float(np.max(v))
    vmin = float(np.min(v))
    vpp = vmax - vmin
    vmean = float(np.mean(v))
    vrms = float(np.sqrt(np.mean(v ** 2)))

    freq = _frequency(t, v, method=freq_method)
    period = (1.0 / freq) if freq and freq > 0 else None
    duty = _duty_cycle(t, v, vmean)
    rise = _transition_time(t, v, vmin, vmax, rising=True)
    fall = _transition_time(t, v, vmin, vmax, rising=False)
    pw, nw = _pulse_widths(t, v, vmean)

    return MeasurementResult(
        vpp=vpp, vmax=vmax, vmin=vmin, vmean=vmean, vrms=vrms,
        frequency=freq, period=period, duty_cycle=duty,
        rise_time=rise, fall_time=fall,
        pos_width=pw, neg_width=nw,
    )


# ── frequency estimation ───────────────────────────────────────────

def _frequency(
    t: np.ndarray, v: np.ndarray, method: str = "zero_crossing"
) -> Optional[float]:
    if method == "fft":
        return _frequency_fft(t, v)
    return _frequency_zero_crossing(t, v)


def _frequency_zero_crossing(t: np.ndarray, v: np.ndarray) -> Optional[float]:
    """Estimate frequency from rising-edge zero crossings at the mean level."""
    mid = float(np.mean(v))
    shifted = v - mid

    # find sign changes (rising)
    signs = np.sign(shifted)
    # ignore exact zeros
    signs[signs == 0] = 1
    crossings = np.where((signs[:-1] < 0) & (signs[1:] > 0))[0]

    if len(crossings) < 2:
        return None

    # interpolate crossing times for better accuracy
    cross_times: list[float] = []
    for i in crossings:
        dv = shifted[i + 1] - shifted[i]
        if abs(dv) < 1e-30:
            cross_times.append(float(t[i]))
        else:
            frac = -shifted[i] / dv
            cross_times.append(float(t[i] + frac * (t[i + 1] - t[i])))

    periods = np.diff(cross_times)
    if len(periods) == 0 or np.mean(periods) <= 0:
        return None
    return float(1.0 / np.mean(periods))


def _frequency_fft(t: np.ndarray, v: np.ndarray) -> Optional[float]:
    """Estimate dominant frequency via FFT."""
    n = len(v)
    if n < 8:
        return None

    dt = float(np.mean(np.diff(t)))
    if dt <= 0:
        return None

    # window the signal to reduce spectral leakage
    windowed = (v - np.mean(v)) * np.hanning(n)
    spectrum = np.abs(np.fft.rfft(windowed))

    freqs = np.fft.rfftfreq(n, d=dt)
    # skip DC bin
    if len(spectrum) > 1:
        spectrum[0] = 0.0
        peak_idx = int(np.argmax(spectrum))
        if spectrum[peak_idx] > 0:
            return float(freqs[peak_idx])
    return None


# ── duty cycle ──────────────────────────────────────────────────────

def _duty_cycle(
    t: np.ndarray, v: np.ndarray, mid: float
) -> Optional[float]:
    """Fraction of total time the signal spends above mid-level."""
    if len(t) < 2:
        return None
    above = v >= mid
    dt = np.diff(t)
    total = float(np.sum(dt))
    if total <= 0:
        return None
    high_time = float(np.sum(dt[above[:-1]]))
    return high_time / total


# ── transition times (10-90%) ───────────────────────────────────────

def _transition_time(
    t: np.ndarray,
    v: np.ndarray,
    vmin: float,
    vmax: float,
    rising: bool,
) -> Optional[float]:
    """
    Measure the average 10→90 % (rising) or 90→10 % (falling)
    transition time.
    """
    if vmax - vmin < 1e-12:
        return None

    lo = vmin + 0.1 * (vmax - vmin)
    hi = vmin + 0.9 * (vmax - vmin)

    transitions: list[float] = []
    in_transition = False
    t_enter: float = 0.0

    if rising:
        for i in range(len(v) - 1):
            if not in_transition and v[i] <= lo < v[i + 1]:
                t_enter = _interp_time(t, v, i, lo)
                in_transition = True
            elif in_transition and v[i] < hi <= v[i + 1]:
                t_exit = _interp_time(t, v, i, hi)
                transitions.append(t_exit - t_enter)
                in_transition = False
            elif in_transition and v[i + 1] < lo:
                in_transition = False  # aborted
    else:
        for i in range(len(v) - 1):
            if not in_transition and v[i] >= hi > v[i + 1]:
                t_enter = _interp_time(t, v, i, hi)
                in_transition = True
            elif in_transition and v[i] > lo >= v[i + 1]:
                t_exit = _interp_time(t, v, i, lo)
                transitions.append(t_exit - t_enter)
                in_transition = False
            elif in_transition and v[i + 1] > hi:
                in_transition = False

    if not transitions:
        return None
    return float(np.mean(transitions))


# ── pulse widths ────────────────────────────────────────────────────

def _pulse_widths(
    t: np.ndarray, v: np.ndarray, mid: float
) -> tuple[Optional[float], Optional[float]]:
    """Average positive and negative pulse widths at mid-level."""
    above = v >= mid
    edges: list[tuple[float, bool]] = []  # (time, is_rising)

    for i in range(len(v) - 1):
        if not above[i] and above[i + 1]:
            edges.append((_interp_time(t, v, i, mid), True))
        elif above[i] and not above[i + 1]:
            edges.append((_interp_time(t, v, i, mid), False))

    pos_widths: list[float] = []
    neg_widths: list[float] = []

    for j in range(len(edges) - 1):
        t1, rising1 = edges[j]
        t2, rising2 = edges[j + 1]
        if rising1 and not rising2:
            pos_widths.append(t2 - t1)
        elif not rising1 and rising2:
            neg_widths.append(t2 - t1)

    pw = float(np.mean(pos_widths)) if pos_widths else None
    nw = float(np.mean(neg_widths)) if neg_widths else None
    return pw, nw


# ── helpers ─────────────────────────────────────────────────────────

def _interp_time(
    t: np.ndarray, v: np.ndarray, i: int, level: float
) -> float:
    """Linear interpolation of the crossing time at *level* between samples i and i+1."""
    dv = v[i + 1] - v[i]
    if abs(dv) < 1e-30:
        return float(t[i])
    frac = (level - v[i]) / dv
    return float(t[i] + frac * (t[i + 1] - t[i]))


_SI_PREFIXES = [
    (1e-15, "f"), (1e-12, "p"), (1e-9, "n"), (1e-6, "µ"),
    (1e-3, "m"), (1.0, ""), (1e3, "k"), (1e6, "M"), (1e9, "G"),
]


def _eng_format(value: float, unit: str, precision: int = 3) -> str:
    """Format *value* with an SI prefix."""
    if value == 0:
        return f"0 {unit}"
    abs_val = abs(value)
    for scale, prefix in _SI_PREFIXES:
        if abs_val < scale * 1000:
            return f"{value / scale:.{precision}g} {prefix}{unit}"
    # fallback
    return f"{value:.{precision}g} {unit}"


def _fmt(value: float, unit: str = "V") -> str:
    return _eng_format(value, unit)


def _fmt_freq(value: float) -> str:
    return _eng_format(value, "Hz")


def _fmt_time(value: float) -> str:
    return _eng_format(value, "s")
