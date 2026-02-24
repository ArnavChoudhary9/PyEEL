"""
Noise analysis.

Computes the spectral noise density (V²/Hz or A²/Hz) at a specified
output node by propagating individual component noise contributions
through the small-signal transfer function.

Noise Sources
-------------
- **Resistors**: thermal (Johnson–Nyquist) noise ``S_v = 4·k·T·R``
- **Diodes**: shot noise ``S_i = 2·q·I_d``
- **BJTs**: shot noise on I_C and I_B, plus thermal on r_bb' (if modelled)

Algorithm
---------
1.  Solve the DC operating point → bias currents and voltages.
2.  Build the linearised small-signal MNA matrix ``G``.
3.  For each frequency ``f``:
    a.  Build ``Y(jω) = G + jωC``  (same as AC analysis).
    b.  For each noisy component, inject a unit noise current and
        compute the transfer impedance to the output.
    c.  Weight by the component's spectral density and sum (RSS).

Result: :class:`NoiseResult` with frequency-dependent noise spectral
density, integrated noise, and per-component breakdown.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

from ..Core.NodeManager import NodeManager
from ..Core.SimulationContext import (
    SimulationConfig, SimulationContext, SimulationMode,
)
from ..Components.Component import Component

logger = logging.getLogger(__name__)

# Physical constants
_K_BOLTZMANN = 1.380649e-23   # J/K
_Q_ELECTRON = 1.602176634e-19  # C


@dataclass
class NoiseResult:
    """Noise analysis result."""
    frequencies: np.ndarray                      # Hz
    output_noise_density: np.ndarray             # V²/Hz (or V/√Hz)
    integrated_noise_vrms: float                 # integrated V_rms
    component_contributions: dict[str, np.ndarray] = field(default_factory=dict)
    # component name → spectral density array


class NoiseAnalysis:
    """
    Linearised noise analysis.

    Parameters
    ----------
    components : list[Component]
        All circuit components.
    node_manager : NodeManager
        Node/index registry.
    config : SimulationConfig
        Simulation configuration (supplies temperature).
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

    def analyze(
        self,
        f_start: float,
        f_stop: float,
        num_points: int = 100,
        *,
        output_node_index: int,
        log_scale: bool = True,
    ) -> NoiseResult:
        """
        Run noise analysis over a frequency sweep.

        Parameters
        ----------
        f_start, f_stop : float
            Frequency range (Hz).
        num_points : int
            Number of frequency points.
        output_node_index : int
            Node index whose voltage noise density is computed.
        log_scale : bool
            Logarithmic frequency spacing.

        Returns
        -------
        NoiseResult
        """
        from ..Components.Passive.Resistor import Resistor
        from ..Components.Passive.Capacitor import Capacitor
        from ..Components.Passive.Inductor import Inductor

        n = self._node_manager.TotalUnknownCount
        nv = self._node_manager.VoltageUnknownCount
        T = self._config.temperature

        if log_scale:
            freqs = np.logspace(np.log10(f_start), np.log10(f_stop), num_points)
        else:
            freqs = np.linspace(f_start, f_stop, num_points)

        # --- Build linearised G matrix ---
        ac_ctx = SimulationContext(
            Mode=SimulationMode.AC, Time=0.0, dt=0.0,
            x_prev=self._x_dc, x_current=self._x_dc,
            integration_method=self._config.integration_method,
            gmin=self._config.gmin,
            source_factor=1.0,
            temperature=T,
        )
        G = np.zeros((n, n), dtype=np.float64)
        b_tmp = np.zeros(n)
        for comp in self._components:
            # Skip reactive elements — they are handled per-frequency
            if isinstance(comp, (Capacitor, Inductor)):
                continue
            comp.Stamp(G, b_tmp, ac_ctx)
        for i in range(nv):
            G[i, i] += self._config.gmin

        # --- Identify noisy components and their spectral densities ---
        noise_sources: list[tuple[str, int | None, int | None, float]] = []
        # (name, node_p, node_n, spectral_density_A²/Hz or V²/Hz)

        for comp in self._components:
            if isinstance(comp, Resistor):
                R = comp.Resistance
                S_i = 4.0 * _K_BOLTZMANN * T / R  # A²/Hz (Norton)
                n1 = comp.Nodes[0].Index
                n2 = comp.Nodes[1].Index
                noise_sources.append((comp.Name, n1, n2, S_i))

        # Shot noise from diodes
        try:
            from ..Components.Semiconductors.Diode import Diode
            for comp in self._components:
                if isinstance(comp, Diode):
                    Id = abs(comp.GetCurrent(self._x_dc))
                    S_i = 2.0 * _Q_ELECTRON * Id
                    n1 = comp.Nodes[0].Index
                    n2 = comp.Nodes[1].Index
                    noise_sources.append((comp.Name, n1, n2, S_i))
        except ImportError:
            pass

        # Shot noise from BJTs (collector and base)
        try:
            from ..Components.Semiconductors.BJT import BJT
            for comp in self._components:
                if isinstance(comp, BJT):
                    Ic = abs(comp.GetCurrent(self._x_dc))
                    Ib = abs(comp.GetBaseCurrent(self._x_dc))
                    # Collector shot noise
                    S_ic = 2.0 * _Q_ELECTRON * Ic
                    nc = comp.Nodes[0].Index
                    ne = comp.Nodes[2].Index
                    noise_sources.append((f"{comp.Name}_Ic", nc, ne, S_ic))
                    # Base shot noise
                    S_ib = 2.0 * _Q_ELECTRON * Ib
                    nb = comp.Nodes[1].Index
                    noise_sources.append((f"{comp.Name}_Ib", nb, ne, S_ib))
        except ImportError:
            pass

        # --- Identify reactive elements ---
        capacitors = [c for c in self._components if isinstance(c, Capacitor)]
        inductors = [c for c in self._components if isinstance(c, Inductor)]

        # --- Sweep ---
        total_noise = np.zeros(len(freqs))
        contrib: dict[str, np.ndarray] = {
            name: np.zeros(len(freqs)) for name, _, _, _ in noise_sources
        }

        for k, f in enumerate(freqs):
            omega = 2.0 * np.pi * f

            Y = G.astype(np.complex128).copy()

            # Capacitors
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

            # Inductors
            for ind in inductors:
                n1 = ind.Nodes[0].Index
                n2 = ind.Nodes[1].Index
                Yl = 1.0 / (1j * omega * ind.Inductance) if omega > 0 else 1e9
                if n1 is not None:
                    Y[n1, n1] += Yl
                    if n2 is not None:
                        Y[n1, n2] -= Yl
                if n2 is not None:
                    Y[n2, n2] += Yl
                    if n1 is not None:
                        Y[n2, n1] -= Yl

            # For each noise source, compute transfer impedance
            try:
                Y_inv = np.linalg.inv(Y)
            except np.linalg.LinAlgError:
                continue

            for name, np_, nn_, Si in noise_sources:
                # Transfer impedance from noise current injection
                # Z_trans = Y^{-1}[out, np] - Y^{-1}[out, nn]
                z_out = 0.0 + 0j
                if np_ is not None:
                    z_out += Y_inv[output_node_index, np_]
                if nn_ is not None:
                    z_out -= Y_inv[output_node_index, nn_]

                # Output-referred noise: S_v_out = |Z_trans|² · S_i
                noise_v2 = float(abs(z_out) ** 2) * Si
                contrib[name][k] = noise_v2
                total_noise[k] += noise_v2

        # Integrate (trapezoidal) to get total RMS noise
        if len(freqs) > 1:
            _trapz = getattr(np, 'trapezoid', getattr(np, 'trapz', None))
            assert _trapz is not None, "numpy has no trapezoid/trapz function"
            integrated = float(_trapz(total_noise, freqs))
            vrms = float(np.sqrt(max(integrated, 0.0)))
        else:
            vrms = 0.0

        return NoiseResult(
            frequencies=freqs,
            output_noise_density=total_noise,
            integrated_noise_vrms=vrms,
            component_contributions=contrib,
        )
