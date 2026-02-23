"""
Small-signal AC analysis.

Linearise the circuit around its DC operating point, replace
reactive elements with their complex impedances, and sweep
frequency to produce Bode-plot data (magnitude + phase vs frequency).

Algorithm
---------
1.  Solve the DC operating point to obtain the bias vector ``x_dc``.
2.  Build the *linearised* MNA matrix ``G`` at the operating point
    (all nonlinear devices contribute their small-signal conductances).
3.  For each frequency ``f`` in the sweep:
    a.  Build ``C`` — the susceptance matrix (capacitors → ``jωC``,
        inductors → ``1/(jωL)``).
    b.  Solve ``(G + jωC) · x_ac = b_ac`` (complex linear system).
    c.  Extract probe values from the complex solution.

The result is a :class:`ACResult` dataclass with frequency,
magnitude (dB) and phase (degrees) arrays.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from ..Core.NodeManager import NodeManager
from ..Core.SimulationContext import (
    SimulationConfig, SimulationContext, SimulationMode,
)
from ..Components.Component import Component
from .LinearSolver import NumpySolver

logger = logging.getLogger(__name__)


@dataclass
class ACResult:
    """Frequency-domain analysis result for one output node."""
    frequencies: np.ndarray       # Hz
    magnitude_dB: np.ndarray      # 20·log10(|H|)
    phase_deg: np.ndarray         # degrees
    complex_response: np.ndarray  # raw H(jω)


class ACAnalysis:
    """
    Small-signal AC frequency sweep.

    Parameters
    ----------
    components : list[Component]
        All circuit components.
    node_manager : NodeManager
        Node/index registry.
    config : SimulationConfig
        Simulation configuration.
    x_dc : np.ndarray
        DC operating-point solution vector.
    """

    def __init__(
        self,
        components: list[Component],
        node_manager: NodeManager,
        config: SimulationConfig,
        x_dc: np.ndarray,
    ):
        self._components = components
        self._node_manager = node_manager
        self._config = config
        self._x_dc = x_dc

    def sweep(
        self,
        f_start: float,
        f_stop: float,
        num_points: int = 100,
        *,
        input_source_name: str | None = None,
        output_node_index: int | None = None,
        input_node_index: int | None = None,
        log_scale: bool = True,
    ) -> ACResult:
        """
        Perform an AC frequency sweep.

        Parameters
        ----------
        f_start, f_stop : float
            Start and stop frequencies (Hz).
        num_points : int
            Number of frequency points.
        input_source_name : str | None
            Name of the AC voltage source providing excitation.
            Its amplitude is treated as 1 V for transfer-function
            computation.  If ``None``, the first voltage source with
            a ``SineWave`` is used.
        output_node_index : int
            Node index whose voltage defines the output.
        input_node_index : int | None
            Node index for computing voltage gain ``H = V_out / V_in``.
            If ``None``, gain is relative to the source (1 V).
        log_scale : bool
            Logarithmic frequency spacing (default ``True``).

        Returns
        -------
        ACResult
        """
        from ..Components.Passive.Capacitor import Capacitor
        from ..Components.Passive.Inductor import Inductor
        from ..Components.Sources.VoltageSource import VoltageSource

        n = self._node_manager.TotalUnknownCount
        nv = self._node_manager.VoltageUnknownCount

        if log_scale:
            freqs = np.logspace(np.log10(f_start), np.log10(f_stop), num_points)
        else:
            freqs = np.linspace(f_start, f_stop, num_points)

        # --- Build linearised G matrix at DC operating point ---
        dc_ctx = SimulationContext(
            Mode=SimulationMode.AC, Time=0.0, dt=0.0,
            x_prev=self._x_dc, x_current=self._x_dc,
            integration_method=self._config.integration_method,
            gmin=self._config.gmin,
            source_factor=1.0,
            temperature=self._config.temperature,
        )

        G = np.zeros((n, n), dtype=np.float64)
        b_dc = np.zeros(n, dtype=np.float64)
        for comp in self._components:
            # Skip reactive elements — they are handled separately
            if isinstance(comp, (Capacitor, Inductor)):
                continue
            comp.Stamp(G, b_dc, dc_ctx)

        # Gmin on voltage nodes
        for i in range(nv):
            G[i, i] += self._config.gmin

        # --- Identify reactive elements ---
        capacitors: list[Capacitor] = []
        inductors: list[Inductor] = []
        for comp in self._components:
            if isinstance(comp, Capacitor):
                capacitors.append(comp)
            elif isinstance(comp, Inductor):
                inductors.append(comp)

        # --- Find the AC source ---
        source_aux_index: int | None = None
        for comp in self._components:
            if isinstance(comp, VoltageSource):
                if input_source_name is None or comp.Name == input_source_name:
                    if comp.AuxIndices:
                        source_aux_index = comp.AuxIndices[0]
                        break

        # --- Sweep ---
        H = np.zeros(len(freqs), dtype=np.complex128)
        solver = NumpySolver()

        for k, f in enumerate(freqs):
            omega = 2.0 * np.pi * f

            # Complex MNA matrix = G + jωC_matrix
            Y = G.astype(np.complex128).copy()
            b_ac = np.zeros(n, dtype=np.complex128)

            # Stamp capacitors: jωC admittance
            for cap in capacitors:
                n1 = cap.Nodes[0].Index
                n2 = cap.Nodes[1].Index
                Yc = 1j * omega * cap.Capacitance
                if n1 is not None:
                    Y[n1, n1] += Yc
                    if n2 is not None:
                        Y[n1, n2] -= Yc
                if n2 is not None:
                    Y[n2, n2] += Yc
                    if n1 is not None:
                        Y[n2, n1] -= Yc

            # Stamp inductors: 1/(jωL) admittance
            for ind in inductors:
                n1 = ind.Nodes[0].Index
                n2 = ind.Nodes[1].Index
                if omega > 0:
                    Yl = 1.0 / (1j * omega * ind.Inductance)
                else:
                    Yl = 1.0 / 1e-9  # DC short
                if n1 is not None:
                    Y[n1, n1] += Yl
                    if n2 is not None:
                        Y[n1, n2] -= Yl
                if n2 is not None:
                    Y[n2, n2] += Yl
                    if n1 is not None:
                        Y[n2, n1] -= Yl

            # AC excitation: 1 V at the source
            if source_aux_index is not None:
                b_ac[source_aux_index] = 1.0

            # Solve complex system
            try:
                x_ac = np.linalg.solve(Y, b_ac)
            except np.linalg.LinAlgError:
                x_ac = np.zeros(n, dtype=np.complex128)

            # Extract transfer function H(jω)
            v_out = x_ac[output_node_index] if output_node_index is not None else 0.0
            if input_node_index is not None:
                v_in = x_ac[input_node_index]
                H[k] = v_out / v_in if abs(v_in) > 1e-30 else 0.0
            else:
                H[k] = v_out  # relative to 1 V source

        # --- Build result ---
        mag = np.abs(H)
        mag_dB = 20.0 * np.log10(np.maximum(mag, 1e-30))
        phase = np.degrees(np.angle(H))

        return ACResult(
            frequencies=freqs,
            magnitude_dB=mag_dB,
            phase_deg=phase,
            complex_response=H,
        )
