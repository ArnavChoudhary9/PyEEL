"""
Harmonic Balance analysis for steady-state nonlinear circuits.

Solves for the periodic steady state of a circuit driven by a
single-tone (or multi-tone) excitation.  The method represents
node voltages as truncated Fourier series and iteratively
balances the currents from the linear sub-network (evaluated in
the frequency domain) with those from the nonlinear sub-network
(evaluated in the time domain via DFT/IDFT).

Usage
-----
::

    from PyEEL.Solver.HarmonicBalance import HarmonicBalance, HBResult
    hb = HarmonicBalance(components, node_manager, config, x_dc)
    result = hb.solve(fundamental=1e6, num_harmonics=7)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..Core.NodeManager import NodeManager
from ..Core.SimulationContext import SimulationContext, SimulationMode, SimulationConfig
from ..Components.Component import Component

logger = logging.getLogger(__name__)


@dataclass
class HBResult:
    """Results from a Harmonic Balance analysis."""
    fundamental: float           # Hz
    num_harmonics: int           # K
    frequencies: np.ndarray      # shape (K+1,) — 0, f, 2f, ...
    spectrum: np.ndarray         # complex, shape (N, K+1) — per node
    converged: bool
    iterations: int
    residual: float


class HarmonicBalance:
    """
    Single-tone Harmonic Balance solver.

    Parameters
    ----------
    components : list[Component]
        Circuit components.
    node_manager : NodeManager
        Node management.
    config : SimulationConfig
        Simulation configuration.
    x_dc : ndarray
        DC operating point solution.
    """

    def __init__(
        self,
        components: list[Component],
        node_manager: NodeManager,
        config: SimulationConfig,
        x_dc: np.ndarray,
    ):
        self._components = components
        self._nm = node_manager
        self._config = config
        self._x_dc = x_dc

    def solve(
        self,
        fundamental: float,
        num_harmonics: int = 7,
        max_iter: int = 200,
        tol: float = 1e-6,
    ) -> HBResult:
        """
        Solve for the periodic steady state.

        Parameters
        ----------
        fundamental : float
            Fundamental frequency in Hz.
        num_harmonics : int
            Number of harmonics K.  Total tones = K+1 (including DC).
        max_iter : int
            Maximum Newton iterations.
        tol : float
            Convergence tolerance on the norm of the residual.

        Returns
        -------
        HBResult
        """
        K = num_harmonics
        N_t = 2 * K + 1          # time samples per period
        N = self._nm.TotalUnknownCount
        N_v = self._nm.VoltageUnknownCount
        f0 = fundamental
        T0 = 1.0 / f0

        freqs = np.arange(K + 1) * f0  # [0, f, 2f, ..., Kf]

        # ── classify components ──────────────────────────────────────
        from ..Components.Passive.Resistor import Resistor
        from ..Components.Passive.Capacitor import Capacitor
        from ..Components.Passive.Inductor import Inductor
        from ..Components.Sources.VoltageSource import VoltageSource
        from ..Components.Sources.Source import Source

        linear_comps = []
        nonlinear_comps = []
        source_comps = []
        for c in self._components:
            if isinstance(c, (VoltageSource, Source)):
                source_comps.append(c)
            elif c.IsNonlinear:
                nonlinear_comps.append(c)
            else:
                linear_comps.append(c)

        # ── Build per-harmonic linear admittance matrices ────────────
        # Y_k for k = 0..K.  For DC (k=0), just conductance.
        # For k>0, Y_k = G + j*ω_k*C
        Y_lin = np.zeros((K + 1, N, N), dtype=complex)

        for k in range(K + 1):
            omega = 2 * np.pi * freqs[k]
            for comp in linear_comps:
                if isinstance(comp, Resistor):
                    n1, n2 = comp.Nodes
                    g = 1.0 / comp.Resistance
                    self._stamp_admittance(Y_lin[k], n1, n2, g)
                elif isinstance(comp, Capacitor):
                    n1, n2 = comp.Nodes
                    y = 1j * omega * comp.Capacitance
                    self._stamp_admittance(Y_lin[k], n1, n2, y)
                elif isinstance(comp, Inductor):
                    # For HB, treat inductor as admittance 1/(jωL)
                    n1, n2 = comp.Nodes
                    if k == 0:
                        # DC: inductor is a short (infinite admittance)
                        # Use a very large admittance (small resistance)
                        y = 1.0 / 1e-9
                    else:
                        y = 1.0 / (1j * omega * comp.Inductance)
                    self._stamp_admittance(Y_lin[k], n1, n2, y)

            # Gmin on diagonal for voltage nodes
            gmin = self._config.gmin
            for i in range(N_v):
                Y_lin[k][i, i] += gmin

        # ── Build source spectrum ────────────────────────────────────
        # Sample sources at N_t time points, then DFT
        time_points = np.linspace(0, T0, N_t, endpoint=False)
        B_source = np.zeros((K + 1, N), dtype=complex)

        ctx = self._make_context(0.0)
        for src in source_comps:
            if isinstance(src, VoltageSource):
                # For voltage source: we handle via auxiliary unknowns
                # Sample the waveform
                src_vals = np.zeros(N_t)
                for ti, t in enumerate(time_points):
                    ctx.Time = t
                    src_vals[ti] = src.EvaluateWaveform(ctx)
                src_spectrum = np.fft.rfft(src_vals) / N_t
                # The VoltageSource stamps KVL via auxiliary index
                aux = src.AuxIndices[0]
                for k in range(K + 1):
                    n1, n2 = src.Nodes
                    if k < len(src_spectrum):
                        if n1.Index is not None:
                            Y_lin[k][aux, n1.Index] = 1
                            Y_lin[k][n1.Index, aux] = 1
                        if n2.Index is not None:
                            Y_lin[k][aux, n2.Index] = -1
                            Y_lin[k][n2.Index, aux] = -1
                        B_source[k][aux] = src_spectrum[k]

        # ── Initialize Fourier coefficients from DC OP ───────────────
        # V_hat[k, n] = Fourier coefficient for harmonic k, node n
        V_hat = np.zeros((K + 1, N), dtype=complex)
        V_hat[0, :] = self._x_dc.astype(complex)

        # ── Newton iteration ────────────────────────────────────────
        converged = False
        iteration = 0
        residual = float('inf')

        for iteration in range(1, max_iter + 1):
            # 1. IDFT: construct time-domain voltage samples
            #    v(t_i) = sum_k V_hat[k] * exp(j*2*pi*k*i/N_t)
            v_time = np.zeros((N_t, N))
            for i in range(N_t):
                v_time[i, :] = np.real(V_hat[0, :])
                for k in range(1, K + 1):
                    phase = 2 * np.pi * k * i / N_t
                    v_time[i, :] += 2 * (
                        np.real(V_hat[k, :]) * np.cos(phase)
                        - np.imag(V_hat[k, :]) * np.sin(phase)
                    )

            # 2. Evaluate nonlinear currents at each time point
            i_nl_time = np.zeros((N_t, N))
            for ti in range(N_t):
                x_sample = v_time[ti, :]
                ctx_t = self._make_context(time_points[ti])
                ctx_t.x_prev = x_sample
                ctx_t.x_current = x_sample

                # Build nonlinear contributions via stamping
                A_nl = np.zeros((N, N))
                b_nl = np.zeros(N)
                for comp in nonlinear_comps:
                    comp.Stamp(A_nl, b_nl, ctx_t)

                # Nonlinear current = A_nl @ x - b_nl (current flowing out)
                i_nl_time[ti, :] = A_nl @ x_sample - b_nl

            # 3. DFT of nonlinear currents
            I_nl_hat = np.zeros((K + 1, N), dtype=complex)
            for n_idx in range(N):
                spectrum = np.fft.rfft(i_nl_time[:, n_idx]) / N_t
                I_nl_hat[:min(K + 1, len(spectrum)), n_idx] = \
                    spectrum[:min(K + 1, len(spectrum))]

            # 4. Form residual: F[k] = Y_lin[k] @ V_hat[k] + I_nl_hat[k] - B_source[k]
            F = np.zeros((K + 1, N), dtype=complex)
            for k in range(K + 1):
                F[k, :] = Y_lin[k] @ V_hat[k, :] + I_nl_hat[k, :] - B_source[k, :]

            residual = float(np.max(np.abs(F)))
            if residual < tol:
                converged = True
                break

            # 5. Solve per-harmonic correction (simplified: ignore
            #    cross-harmonic Jacobian terms from nonlinear elements)
            #    J_k ≈ Y_lin[k] + G_nl  (linearized NL conductance at DC)
            # Compute G_nl from the DC operating point
            G_nl = np.zeros((N, N))
            b_dummy = np.zeros(N)
            ctx_dc = self._make_context(0.0)
            ctx_dc.x_prev = self._x_dc
            ctx_dc.x_current = self._x_dc
            for comp in nonlinear_comps:
                comp.Stamp(G_nl, b_dummy, ctx_dc)

            for k in range(K + 1):
                J_k = Y_lin[k] + G_nl.astype(complex)
                try:
                    delta = np.linalg.solve(J_k, -F[k, :])
                    V_hat[k, :] += delta
                except np.linalg.LinAlgError:
                    logger.warning("HB: singular Jacobian at harmonic %d", k)

        # ── Build result ─────────────────────────────────────────────
        return HBResult(
            fundamental=f0,
            num_harmonics=K,
            frequencies=freqs,
            spectrum=V_hat,
            converged=converged,
            iterations=iteration,
            residual=residual,
        )

    @staticmethod
    def _stamp_admittance(Y, n1, n2, y):
        """Stamp a 2-terminal admittance y between nodes n1 and n2."""
        i1 = n1.Index if n1.Index is not None else None
        i2 = n2.Index if n2.Index is not None else None
        if i1 is not None:
            Y[i1, i1] += y
        if i2 is not None:
            Y[i2, i2] += y
        if i1 is not None and i2 is not None:
            Y[i1, i2] -= y
            Y[i2, i1] -= y

    def _make_context(self, time: float) -> SimulationContext:
        """Create a context for a given time point."""
        return SimulationContext(
            Mode=SimulationMode.TRANSIENT,
            Time=time,
            dt=1e-9,
            x_prev=self._x_dc,
            x_current=self._x_dc,
            integration_method=self._config.integration_method,
            gmin=self._config.gmin,
            source_factor=1.0,
            temperature=self._config.temperature,
        )
