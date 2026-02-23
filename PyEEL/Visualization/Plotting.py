"""
Static plotting helpers for analysis results.

Each function accepts a result dataclass from one of the analysis
engines and produces a **matplotlib** figure.  All functions return
the ``(fig, axes)`` tuple so callers can further customise the plot
before showing or saving.

Dependencies: ``matplotlib`` (must be installed separately).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ..Solver.ACAnalysis import ACResult
    from ..Solver.NoiseAnalysis import NoiseResult
    from ..Solver.HarmonicBalance import HBResult
    from ..Simulation.MonteCarlo import MonteCarloResult
    from ..Simulation.ParameterSweep import SweepResult


# ── helpers ──────────────────────────────────────────────────────────

def _import_plt():
    """Lazily import matplotlib so the rest of PyEEL doesn't require it."""
    try:
        import matplotlib.pyplot as plt
        return plt
    except ImportError as exc:
        raise ImportError(
            "matplotlib is required for plotting. "
            "Install it with:  pip install matplotlib"
        ) from exc


# =====================================================================
#  AC Analysis — Bode plot
# =====================================================================

def plot_bode(
    result: ACResult,
    *,
    title: str = "Bode Plot",
    figsize: tuple[float, float] = (10, 6),
    mag_label: str = "Magnitude (dB)",
    phase_label: str = "Phase (°)",
    show: bool = True,
):
    """
    Plot a Bode diagram (magnitude + phase) from an :class:`ACResult`.

    Parameters
    ----------
    result : ACResult
        Output of :meth:`Circuit.RunAC` or :meth:`ACAnalysis.sweep`.
    title : str
        Figure title.
    figsize : tuple
        Matplotlib figure size.
    mag_label, phase_label : str
        Y-axis labels.
    show : bool
        If *True*, calls ``plt.show()`` before returning.

    Returns
    -------
    (fig, (ax_mag, ax_phase))
    """
    plt = _import_plt()
    fig, (ax_mag, ax_phase) = plt.subplots(2, 1, sharex=True, figsize=figsize)

    freqs = result.frequencies
    ax_mag.semilogx(freqs, result.magnitude_dB)
    ax_mag.set_ylabel(mag_label)
    ax_mag.set_title(title)
    ax_mag.grid(True, which="both", ls="--", alpha=0.5)

    ax_phase.semilogx(freqs, result.phase_deg)
    ax_phase.set_ylabel(phase_label)
    ax_phase.set_xlabel("Frequency (Hz)")
    ax_phase.grid(True, which="both", ls="--", alpha=0.5)

    fig.tight_layout()
    if show:
        plt.show()
    return fig, (ax_mag, ax_phase)


# =====================================================================
#  Noise Analysis — spectral density
# =====================================================================

def plot_noise_spectrum(
    result: NoiseResult,
    *,
    title: str = "Noise Spectral Density",
    figsize: tuple[float, float] = (10, 5),
    show_components: bool = True,
    ylabel: str = r"Noise density (V²/Hz)",
    show: bool = True,
):
    """
    Plot noise spectral density from a :class:`NoiseResult`.

    Parameters
    ----------
    result : NoiseResult
        Output of :meth:`Circuit.RunNoise` or :meth:`NoiseAnalysis.analyze`.
    title : str
        Figure title.
    figsize : tuple
        Figure size.
    show_components : bool
        If *True* and per-component contributions are available, overlay
        them as individual traces.
    ylabel : str
        Y-axis label.
    show : bool
        If *True*, calls ``plt.show()``.

    Returns
    -------
    (fig, ax)
    """
    plt = _import_plt()
    fig, ax = plt.subplots(figsize=figsize)

    freqs = result.frequencies
    ax.loglog(freqs, result.output_noise_density, "k-", linewidth=2,
              label="Total output noise")

    if show_components and result.component_contributions:
        for name, density in result.component_contributions.items():
            ax.loglog(freqs, density, "--", alpha=0.7, label=name)
        ax.legend(fontsize=8, loc="best")

    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel(ylabel)
    ax.set_title(f"{title}  (integrated = {result.integrated_noise_vrms:.3e} Vrms)")
    ax.grid(True, which="both", ls="--", alpha=0.5)

    fig.tight_layout()
    if show:
        plt.show()
    return fig, ax


# =====================================================================
#  Monte Carlo — histogram
# =====================================================================

def plot_monte_carlo(
    result: MonteCarloResult,
    *,
    title: str = "Monte Carlo Distribution",
    figsize: tuple[float, float] = (10, 5),
    bins: int | str = "auto",
    xlabel: str = "Measured value",
    show_stats: bool = True,
    show: bool = True,
):
    """
    Plot a histogram of Monte Carlo results.

    Parameters
    ----------
    result : MonteCarloResult
        Output of :meth:`MonteCarlo.run`.
    title : str
        Figure title.
    figsize : tuple
        Figure size.
    bins : int or str
        Passed to ``plt.hist``.
    xlabel : str
        X-axis label.
    show_stats : bool
        If *True*, annotate mean, std, and 5th/95th percentiles.
    show : bool
        If *True*, calls ``plt.show()``.

    Returns
    -------
    (fig, ax)
    """
    plt = _import_plt()
    fig, ax = plt.subplots(figsize=figsize)

    ax.hist(result.values, bins=bins, edgecolor="black", alpha=0.75)

    if show_stats:
        ymax = ax.get_ylim()[1]
        ax.axvline(result.mean, color="red", linestyle="-", linewidth=1.5,
                   label=f"Mean = {result.mean:.4g}")
        ax.axvline(result.mean - result.std, color="orange", linestyle="--",
                   linewidth=1, label=f"±1σ = {result.std:.4g}")
        ax.axvline(result.mean + result.std, color="orange", linestyle="--",
                   linewidth=1)
        ax.axvline(result.percentile_5, color="blue", linestyle=":",
                   linewidth=1, label=f"5th = {result.percentile_5:.4g}")
        ax.axvline(result.percentile_95, color="blue", linestyle=":",
                   linewidth=1, label=f"95th = {result.percentile_95:.4g}")
        ax.legend(fontsize=9, loc="best")

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Count")
    ax.set_title(f"{title}  (N = {result.num_runs})")
    ax.grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    if show:
        plt.show()
    return fig, ax


# =====================================================================
#  Parameter Sweep — line / heatmap
# =====================================================================

def plot_sweep(
    result: SweepResult,
    *,
    title: str = "Parameter Sweep",
    figsize: tuple[float, float] = (10, 5),
    ylabel: str = "Measured value",
    log_x: bool = False,
    show: bool = True,
):
    """
    Plot parameter sweep results.

    * **Single parameter**: line plot (value vs. parameter).
    * **Dual parameter**: 2-D heatmap.

    Parameters
    ----------
    result : SweepResult
        Output of :meth:`ParameterSweep.run`.
    title : str
        Figure title.
    figsize : tuple
        Figure size.
    ylabel : str
        Y-axis label (single-parameter mode only).
    log_x : bool
        If *True*, use logarithmic x-axis (single-param mode).
    show : bool
        If *True*, calls ``plt.show()``.

    Returns
    -------
    (fig, ax)
    """
    plt = _import_plt()
    param_names = list(result.sweep_values.keys())
    measured = np.asarray(result.measured)

    if measured.ndim == 1:
        # Single-parameter sweep
        fig, ax = plt.subplots(figsize=figsize)
        x = result.sweep_values[param_names[0]]
        plot_fn = ax.semilogx if log_x else ax.plot
        plot_fn(x, measured, "o-", markersize=3)
        ax.set_xlabel(param_names[0])
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, ls="--", alpha=0.5)
    elif measured.ndim == 2:
        # Dual-parameter heatmap
        fig, ax = plt.subplots(figsize=figsize)
        x = result.sweep_values[param_names[0]]
        y = result.sweep_values[param_names[1]]
        im = ax.pcolormesh(x, y, measured.T, shading="auto")
        fig.colorbar(im, ax=ax, label=ylabel)
        ax.set_xlabel(param_names[0])
        ax.set_ylabel(param_names[1])
        ax.set_title(title)
    else:
        raise ValueError(f"Cannot plot {measured.ndim}-D sweep result.")

    fig.tight_layout()
    if show:
        plt.show()
    return fig, ax


# =====================================================================
#  Harmonic Balance — frequency spectrum
# =====================================================================

def plot_harmonic_spectrum(
    result: HBResult,
    *,
    node_index: int = 0,
    title: str = "Harmonic Spectrum",
    figsize: tuple[float, float] = (10, 5),
    show: bool = True,
):
    """
    Plot harmonic magnitudes from a :class:`HBResult`.

    Parameters
    ----------
    result : HBResult
        Output of :meth:`Circuit.RunHarmonicBalance` or
        :meth:`HarmonicBalance.solve`.
    node_index : int
        Which node's spectrum to plot (column index in
        ``result.spectrum``).  Default 0 (first node).
    title : str
        Figure title.
    figsize : tuple
        Figure size.
    show : bool
        If *True*, calls ``plt.show()``.

    Returns
    -------
    (fig, ax)
    """
    plt = _import_plt()
    fig, ax = plt.subplots(figsize=figsize)

    freqs = result.frequencies
    magnitudes = np.abs(result.spectrum[:, node_index])

    ax.bar(range(len(freqs)), magnitudes, color="steelblue", edgecolor="black")
    ax.set_xticks(range(len(freqs)))
    ax.set_xticklabels([f"{f:.0f}" for f in freqs], rotation=45, ha="right")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Magnitude")

    status = "converged" if result.converged else "NOT converged"
    ax.set_title(f"{title}  ({status}, {result.iterations} iters, "
                 f"residual={result.residual:.2e})")
    ax.grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    if show:
        plt.show()
    return fig, ax


# =====================================================================
#  Transient waveform — generic time-domain plot
# =====================================================================

def plot_transient(
    time: np.ndarray,
    signals: dict[str, np.ndarray],
    *,
    title: str = "Transient Simulation",
    figsize: tuple[float, float] = (10, 5),
    ylabel: str = "Voltage / Current",
    show: bool = True,
):
    """
    Plot one or more time-domain waveforms.

    Parameters
    ----------
    time : np.ndarray
        Time array (seconds).
    signals : dict[str, np.ndarray]
        Mapping from label to data array.
    title : str
        Figure title.
    figsize : tuple
        Figure size.
    ylabel : str
        Y-axis label.
    show : bool
        If *True*, calls ``plt.show()``.

    Returns
    -------
    (fig, ax)
    """
    plt = _import_plt()
    fig, ax = plt.subplots(figsize=figsize)

    for label, data in signals.items():
        ax.plot(time, data, label=label)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(fontsize=9, loc="best")
    ax.grid(True, ls="--", alpha=0.5)

    fig.tight_layout()
    if show:
        plt.show()
    return fig, ax
