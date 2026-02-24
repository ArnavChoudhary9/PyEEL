"""
Monte Carlo analysis engine.

Randomizes component parameters (tolerances and device variations)
across multiple simulation runs, collecting statistical distributions
of key outputs.

Usage
-----
::

    from PyEEL.Simulation.MonteCarlo import MonteCarlo, Tolerance

    mc = MonteCarlo(circuit)
    mc.add_tolerance(R1, "Resistance", Tolerance.percent(5))
    mc.add_tolerance(C1, "Capacitance", Tolerance.percent(10))
    mc.add_tolerance(Q1, "BF", Tolerance.gaussian(mean=100, std=20))
    result = mc.run(num_runs=1000, measure=lambda ckt, x: x[n_out.Index])
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Any

import numpy as np

from ..Components.Component import Component
from ..Simulation.Circuit import Circuit

logger = logging.getLogger(__name__)


@dataclass
class Tolerance:
    """
    Describes how a parameter varies across Monte Carlo runs.

    Factory methods provide common distribution types.
    """
    distribution: str           # "uniform", "gaussian", "uniform_pct", "gaussian_pct"
    params: dict[str, float]    # distribution-specific parameters

    @staticmethod
    def percent(pct: float) -> Tolerance:
        """Uniform ±pct% around the nominal value."""
        return Tolerance("uniform_pct", {"pct": pct})

    @staticmethod
    def gaussian_percent(pct: float) -> Tolerance:
        """Gaussian with 3σ = pct% of nominal."""
        return Tolerance("gaussian_pct", {"pct": pct})

    @staticmethod
    def uniform(low: float, high: float) -> Tolerance:
        """Uniform distribution between *low* and *high*."""
        return Tolerance("uniform", {"low": low, "high": high})

    @staticmethod
    def gaussian(mean: float, std: float) -> Tolerance:
        """Gaussian with given mean and standard deviation."""
        return Tolerance("gaussian", {"mean": mean, "std": std})


@dataclass
class MonteCarloResult:
    """Results from a Monte Carlo analysis run."""
    num_runs: int
    values: np.ndarray        # shape (num_runs,) — measured output per run
    mean: float
    std: float
    min: float
    max: float
    percentile_5: float
    percentile_95: float
    parameter_samples: dict[str, np.ndarray] = field(default_factory=dict)
    # component_name.param → array of sampled values


class MonteCarlo:
    """
    Monte Carlo analysis engine.

    Parameters
    ----------
    circuit : Circuit
        A finalized circuit.  Its components will have parameters
        temporarily modified for each run.
    """

    def __init__(self, circuit: Circuit):
        self._circuit = circuit
        self._tolerances: list[tuple[Component, str, Tolerance]] = []

    def add_tolerance(
        self,
        component: Component,
        parameter: str,
        tolerance: Tolerance,
    ) -> None:
        """
        Register a parameter to be randomized.

        Parameters
        ----------
        component : Component
            The component whose parameter will vary.
        parameter : str
            Name of the *private* attribute (without leading ``_``),
            e.g. ``"Resistance"``, ``"Capacitance"``, ``"BF"``, ``"Is"``.
        tolerance : Tolerance
            Distribution description.
        """
        self._tolerances.append((component, parameter, tolerance))

    def run(
        self,
        num_runs: int = 100,
        *,
        measure: Callable[[Circuit, np.ndarray], float] | None = None,
        seed: int | None = None,
    ) -> MonteCarloResult:
        """
        Execute the Monte Carlo sweep.

        Parameters
        ----------
        num_runs : int
            Number of random trials.
        measure : callable
            ``measure(circuit, x_dc) -> float`` — extracts the
            metric of interest from each run's DC solution.
            If ``None``, uses ``np.max(np.abs(x_dc))``.
        seed : int | None
            Random seed for reproducibility.

        Returns
        -------
        MonteCarloResult
        """
        rng = np.random.default_rng(seed)
        ckt = self._circuit
        values = np.zeros(num_runs)
        param_samples: dict[str, np.ndarray] = {}

        if measure is None:
            def _default_measure(c, x):
                return float(np.max(np.abs(x)))
            measure = _default_measure

        # Save nominal values — prefer the public property (so setters fire).
        nominals: list[tuple[Component, str, float]] = []
        for comp, param, tol in self._tolerances:
            # Check public property first, then private
            if hasattr(comp, param):
                attr = param
                nominal = getattr(comp, param)
            elif hasattr(comp, f"_{param}"):
                attr = f"_{param}"
                nominal = getattr(comp, attr)
            else:
                raise ValueError(
                    f"Component '{comp.Name}' has no attribute '{param}' or '_{param}'"
                )
            nominals.append((comp, attr, float(nominal)))
            key = f"{comp.Name}.{param}"
            param_samples[key] = np.zeros(num_runs)

        for run in range(num_runs):
            # Randomize parameters
            for idx, (comp, param, tol) in enumerate(self._tolerances):
                _, attr, nominal = nominals[idx]
                val = self._sample(rng, nominal, tol)
                setattr(comp, attr, val)
                key = f"{comp.Name}.{param}"
                param_samples[key][run] = val

            # Solve DC operating point
            ckt.Reset()
            try:
                x_dc = ckt.SolveDCOperatingPoint()
                values[run] = measure(ckt, x_dc)
            except Exception as exc:
                logger.warning("Monte Carlo run %d failed: %s", run, exc)
                values[run] = float('nan')

        # Restore nominal values
        for comp, attr, nominal in nominals:
            setattr(comp, attr, nominal)

        # Compute statistics
        valid = values[np.isfinite(values)]
        if len(valid) == 0:
            return MonteCarloResult(
                num_runs=num_runs, values=values,
                mean=float('nan'), std=float('nan'),
                min=float('nan'), max=float('nan'),
                percentile_5=float('nan'), percentile_95=float('nan'),
                parameter_samples=param_samples,
            )

        return MonteCarloResult(
            num_runs=num_runs,
            values=values,
            mean=float(np.mean(valid)),
            std=float(np.std(valid)),
            min=float(np.min(valid)),
            max=float(np.max(valid)),
            percentile_5=float(np.percentile(valid, 5)),
            percentile_95=float(np.percentile(valid, 95)),
            parameter_samples=param_samples,
        )

    @staticmethod
    def _sample(rng, nominal: float, tol: Tolerance) -> float:
        """Draw a single random sample for the given tolerance spec."""
        d = tol.distribution
        p = tol.params

        if d == "uniform_pct":
            delta = nominal * p["pct"] / 100.0
            return float(rng.uniform(nominal - delta, nominal + delta))
        elif d == "gaussian_pct":
            sigma = nominal * p["pct"] / 300.0  # 3σ = pct%
            return float(rng.normal(nominal, sigma))
        elif d == "uniform":
            return float(rng.uniform(p["low"], p["high"]))
        elif d == "gaussian":
            return float(rng.normal(p["mean"], p["std"]))
        else:
            raise ValueError(f"Unknown distribution: {d}")
