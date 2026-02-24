"""
Parameter sweep engine.

Sweeps one or more component parameters across a specified range,
running a DC (or AC) analysis at each point and collecting results.

Usage
-----
::

    from PyEEL.Simulation.ParameterSweep import ParameterSweep

    sweep = ParameterSweep(circuit)
    sweep.add_parameter(R1, "Resistance", start=1e3, stop=10e3, num=50)
    result = sweep.run(measure=lambda ckt, x: x[n_out.Index])
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from ..Components.Component import Component
from ..Simulation.Circuit import Circuit

logger = logging.getLogger(__name__)


@dataclass
class _ParamSpec:
    component: Component
    parameter: str
    attr_name: str          # actual attribute to set (e.g. "_Resistance")
    values: np.ndarray      # sweep values
    nominal: float          # original value (for restoration)


@dataclass
class SweepResult:
    """Results from a parameter sweep."""
    sweep_values: dict[str, np.ndarray]  # "R1.Resistance" → array
    measured: np.ndarray                  # shape depends on number of swept params
    # For a single-param sweep: shape (num_points,)
    # For a dual-param sweep:   shape (num_A, num_B)


class ParameterSweep:
    """
    Sweep one or two component parameters and measure an output.

    Parameters
    ----------
    circuit : Circuit
        A finalized circuit.
    """

    def __init__(self, circuit: Circuit):
        self._circuit = circuit
        self._specs: list[_ParamSpec] = []

    def add_parameter(
        self,
        component: Component,
        parameter: str,
        *,
        start: float,
        stop: float,
        num: int = 50,
        log_scale: bool = False,
    ) -> None:
        """
        Register a parameter to sweep.

        Parameters
        ----------
        component : Component
            Component whose parameter is swept.
        parameter : str
            Name of the attribute, e.g. ``"Resistance"``.
        start, stop : float
            Range limits (inclusive).
        num : int
            Number of sweep points (default 50).
        log_scale : bool
            If True, use logarithmic spacing.
        """
        # Prefer public property (so setter fires)
        if hasattr(component, parameter):
            attr = parameter
            nominal = getattr(component, parameter)
        elif hasattr(component, f"_{parameter}"):
            attr = f"_{parameter}"
            nominal = getattr(component, attr)
        else:
            raise ValueError(
                f"Component '{component.Name}' has no attribute "
                f"'{parameter}' or '_{parameter}'"
            )

        if log_scale:
            values = np.logspace(np.log10(start), np.log10(stop), num)
        else:
            values = np.linspace(start, stop, num)

        self._specs.append(_ParamSpec(
            component=component,
            parameter=parameter,
            attr_name=attr,
            values=values,
            nominal=float(nominal),
        ))

    def add_parameter_list(
        self,
        component: Component,
        parameter: str,
        values: list[float] | np.ndarray,
    ) -> None:
        """Register a parameter with an explicit list of values."""
        if hasattr(component, parameter):
            attr = parameter
            nominal = getattr(component, parameter)
        elif hasattr(component, f"_{parameter}"):
            attr = f"_{parameter}"
            nominal = getattr(component, attr)
        else:
            raise ValueError(
                f"Component '{component.Name}' has no attribute "
                f"'{parameter}' or '_{parameter}'"
            )
        self._specs.append(_ParamSpec(
            component=component,
            parameter=parameter,
            attr_name=attr,
            values=np.asarray(values, dtype=float),
            nominal=float(nominal),
        ))

    def run(
        self,
        *,
        measure: Callable[[Circuit, np.ndarray], float] | None = None,
    ) -> SweepResult:
        """
        Execute the sweep.

        Parameters
        ----------
        measure : callable
            ``measure(circuit, x_dc) -> float``.
            Defaults to ``max(abs(x_dc))``.

        Returns
        -------
        SweepResult
        """
        if not self._specs:
            raise RuntimeError("No parameters added to sweep.")
        if len(self._specs) > 2:
            raise RuntimeError("At most 2 nested sweep parameters are supported.")

        if measure is None:
            def _default_measure(c, x):
                return float(np.max(np.abs(x)))
            measure = _default_measure

        ckt = self._circuit
        sweep_values: dict[str, np.ndarray] = {}

        if len(self._specs) == 1:
            spec = self._specs[0]
            key = f"{spec.component.Name}.{spec.parameter}"
            sweep_values[key] = spec.values
            result = np.zeros(len(spec.values))

            for i, val in enumerate(spec.values):
                setattr(spec.component, spec.attr_name, val)
                ckt.Reset()
                try:
                    x = ckt.SolveDCOperatingPoint()
                    result[i] = measure(ckt, x)
                except Exception as exc:
                    logger.warning("Sweep point %d (%.4g) failed: %s", i, val, exc)
                    result[i] = float('nan')

            # Restore
            setattr(spec.component, spec.attr_name, spec.nominal)
            return SweepResult(sweep_values=sweep_values, measured=result)

        else:
            s0, s1 = self._specs
            k0 = f"{s0.component.Name}.{s0.parameter}"
            k1 = f"{s1.component.Name}.{s1.parameter}"
            sweep_values[k0] = s0.values
            sweep_values[k1] = s1.values
            result = np.zeros((len(s0.values), len(s1.values)))

            for i, v0 in enumerate(s0.values):
                setattr(s0.component, s0.attr_name, v0)
                for j, v1 in enumerate(s1.values):
                    setattr(s1.component, s1.attr_name, v1)
                    ckt.Reset()
                    try:
                        x = ckt.SolveDCOperatingPoint()
                        result[i, j] = measure(ckt, x)
                    except Exception as exc:
                        logger.warning(
                            "Sweep (%d,%d) failed: %s", i, j, exc
                        )
                        result[i, j] = float('nan')

            # Restore
            setattr(s0.component, s0.attr_name, s0.nominal)
            setattr(s1.component, s1.attr_name, s1.nominal)
            return SweepResult(sweep_values=sweep_values, measured=result)
