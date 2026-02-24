"""
Circuit — top-level simulation container.

Owns nodes, components, probes, and drives the transient simulation
loop by delegating to focused helper classes.
"""

from __future__ import annotations

import logging
import numpy as np

from ..Core.NodeManager import NodeManager
from ..Core.SimulationContext import (
    SimulationContext, SimulationMode, SimulationConfig,
)
from ..Components.Component import Component
from ..Solver.LinearSolver import LinearSolver
from ..Solver.MNASystemBuilder import MNASystemBuilder
from ..Solver.NewtonRaphson import NewtonRaphsonSolver
from ..Solver.DCOperatingPoint import DCOperatingPointSolver
from .TopologyValidator import TopologyValidator
from .EnergyChecker import EnergyChecker
from .AdaptiveTimestep import AdaptiveTimestep

# Probe is imported lazily / via TYPE_CHECKING to avoid circular deps
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..Visualization.Probe import Probe

logger = logging.getLogger(__name__)


class Circuit:
    """
    Top-level container that owns nodes, components, probes, and drives
    the transient simulation loop.

    Typical usage
    -------------
    1. Create nodes via ``circuit.NodeManager.AddNode(...)``.
    2. Add components via ``circuit.AddComponent(...)``.
    3. Attach probes via ``circuit.AddProbe(...)``.
    4. Call ``circuit.Finalize()`` to lock the topology.
    5. Repeatedly call ``circuit.Simulate(dt)`` to advance time.
    """

    _NodeManager: NodeManager
    _Components: list[Component]
    _Probes: list  # list[Probe]
    _Solver: LinearSolver
    _Finalized: bool
    _config: SimulationConfig

    __T: float
    __x_prev: np.ndarray | None
    __dc_solved: bool
    __step_count: int
    _has_nonlinear: bool
    _initial_guesses: dict[int, float]  # node_index → voltage

    def __init__(self, solver: LinearSolver,
                 config: SimulationConfig | None = None):
        self._NodeManager = NodeManager()
        self._Components: list[Component] = []
        self._Probes: list = []
        self._Solver = solver
        self._Finalized = False
        self._config = config if config is not None else SimulationConfig()

        self.__T = 0.0
        self.__x_prev = None
        self.__dc_solved = False
        self.__step_count = 0
        self._has_nonlinear = False
        self._initial_guesses: dict[int, float] = {}
        self._event_detector = None  # EventDetector | None

        # Initialised in Finalize()
        self._system_builder: MNASystemBuilder | None = None
        self._nr_solver: NewtonRaphsonSolver | None = None
        self._adaptive: AdaptiveTimestep | None = None

    # ── properties ──────────────────────────────────────────────────
    @property
    def NodeManager(self) -> NodeManager:
        """Access the circuit's node registry."""
        return self._NodeManager

    @property
    def Time(self) -> float:
        """Current simulation time in seconds."""
        return self.__T

    @property
    def Probes(self) -> list:
        """All measurement probes attached to this circuit."""
        return self._Probes

    @property
    def Config(self) -> SimulationConfig:
        """Simulation configuration (read-only reference)."""
        return self._config

    @property
    def RecommendedDt(self) -> float | None:
        """Recommended dt from adaptive timestep heuristic (``None`` if disabled)."""
        if self._adaptive is not None:
            return self._adaptive.recommended_dt
        return None

    # ── setup ───────────────────────────────────────────────────────
    def Reset(self) -> None:
        """Reset the simulation clock, previous solution, and all probes."""
        self.__T = 0.0
        self.__x_prev = None
        self.__dc_solved = False
        self.__step_count = 0
        if self._adaptive is not None:
            self._adaptive._recommended_dt = None

        for probe in self._Probes:
            probe.Clear()

    def AddComponent(self, component: Component) -> None:
        """Add a component **before** :meth:`Finalize` is called."""
        if self._Finalized:
            raise RuntimeError("Cannot add component to a finalized circuit.")
        self._Components.append(component)

    def AddProbe(self, probe) -> None:
        """Attach a measurement probe (can be done before or after finalize)."""
        self._Probes.append(probe)

    def SetEventDetector(self, detector) -> None:
        """Attach an :class:`EventDetector` to the simulation loop."""
        self._event_detector = detector

    def SetInitialGuess(self, node, voltage: float) -> None:
        """
        Set an initial node-voltage guess for the DC operating point.

        Parameters
        ----------
        node : Node
            A node previously created via ``NodeManager.AddNode``.
        voltage : float
            Initial guess voltage (V).

        The guess is injected as the starting point for the DC solver's
        Newton-Raphson iteration, improving convergence for circuits that
        are sensitive to initial conditions.
        """
        from ..Core.Node import Node as NodeCls
        if not isinstance(node, NodeCls):
            raise TypeError(f"Expected a Node, got {type(node).__name__}")
        if node.Index is None:
            raise ValueError("Cannot set initial guess for ground node.")
        self._initial_guesses[node.Index] = voltage

    def GetSolution(self) -> np.ndarray | None:
        """Return the most recent solution vector, or ``None`` if unsolved."""
        return self.__x_prev
    def Finalize(self) -> None:
        """
        Freeze the topology, register auxiliary unknowns, run topology
        checks, and pre-allocate MNA arrays.  Must be called exactly
        once before :meth:`Simulate`.
        """
        if self._Finalized:
            raise RuntimeError("Circuit is already finalized.")

        self._NodeManager.Freeze()

        for component in self._Components:
            component.RegisterUnknowns(self._NodeManager)

        self._Finalized = True

        # Reusable simulation context (mutated each step)
        n = self._NodeManager.TotalUnknownCount
        self._context = SimulationContext(
            Mode=SimulationMode.TRANSIENT, Time=0.0, dt=0.0,
            integration_method=self._config.integration_method,
            gmin=self._config.gmin,
            temperature=self._config.temperature,
        )

        # Topology sanity checks
        TopologyValidator.validate(self._Components, self._NodeManager)

        # Detect nonlinear components
        self._has_nonlinear = any(c.IsNonlinear for c in self._Components)

        # Solver infrastructure
        self._system_builder = MNASystemBuilder(
            self._Components, self._NodeManager, self._config.gmin,
        )
        self._nr_solver = NewtonRaphsonSolver(
            self._system_builder, self._Solver, self._config,
        )
        self._adaptive = AdaptiveTimestep(self._config)

    # ── DC operating point ──────────────────────────────────────────
    def SolveDCOperatingPoint(self) -> np.ndarray:
        """
        Solve the DC operating point and store the result as the
        initial condition for the transient simulation.

        Returns the DC solution vector.
        """
        if not self._Finalized:
            raise RuntimeError("Circuit must be finalized first.")

        dc_solver = DCOperatingPointSolver(
            self._Components, self._NodeManager,
            self._Solver, self._config, self._has_nonlinear,
            initial_guesses=self._initial_guesses,
        )

        x_dc = dc_solver.solve()

        # Inject capacitor / inductor initial conditions
        from ..Components.Passive.Capacitor import Capacitor as _Cap
        from ..Components.Passive.Inductor import Inductor as _Ind
        for comp in self._Components:
            if isinstance(comp, _Cap) and comp.InitialVoltage is not None:
                n1 = comp.Nodes[0].Index
                n2 = comp.Nodes[1].Index
                v_ic = comp.InitialVoltage
                if n1 is not None:
                    x_dc[n1] = v_ic + (x_dc[n2] if n2 is not None else 0.0)

        self.__x_prev = x_dc.copy()
        self.__dc_solved = True

        # Propagate DC solution into component states
        dc_ctx = SimulationContext(
            Mode=SimulationMode.DC, Time=0.0, dt=0.0,
            x_prev=None, x_current=x_dc,
            integration_method=self._config.integration_method,
            gmin=self._config.gmin,
        )
        for comp in self._Components:
            comp.UpdateState(x_dc, dc_ctx)

        logger.info("DC operating point complete.")
        return x_dc

    # ── AC analysis ─────────────────────────────────────────────────
    def RunAC(
        self,
        f_start: float,
        f_stop: float,
        num_points: int = 100,
        *,
        input_source_name: str | None = None,
        output_node_index: int | None = None,
        input_node_index: int | None = None,
        log_scale: bool = True,
    ):
        """
        Perform a small-signal AC frequency sweep.

        The circuit must be finalized.  If the DC operating point has
        not yet been solved, it is computed automatically.

        Returns an :class:`ACResult` with ``frequencies``,
        ``magnitude_dB``, ``phase_deg``, and ``complex_response``.
        """
        from ..Solver.ACAnalysis import ACAnalysis

        if not self._Finalized:
            raise RuntimeError("Circuit must be finalized first.")
        if self.__x_prev is None:
            self.SolveDCOperatingPoint()

        assert self.__x_prev is not None
        ac = ACAnalysis(
            self._Components, self._NodeManager, self._config, self.__x_prev,
        )
        return ac.sweep(
            f_start, f_stop, num_points,
            input_source_name=input_source_name,
            output_node_index=output_node_index,
            input_node_index=input_node_index,
            log_scale=log_scale,
        )

    # ── noise analysis ──────────────────────────────────────────────
    def RunNoise(
        self,
        f_start: float,
        f_stop: float,
        num_points: int = 100,
        *,
        output_node_index: int,
        log_scale: bool = True,
    ):
        """
        Perform a noise analysis over a frequency sweep.

        Computes output-referred noise spectral density (V²/Hz),
        integrated RMS noise, and per-component breakdown.

        Returns a :class:`NoiseResult`.
        """
        from ..Solver.NoiseAnalysis import NoiseAnalysis

        if not self._Finalized:
            raise RuntimeError("Circuit must be finalized first.")
        if self.__x_prev is None:
            self.SolveDCOperatingPoint()

        assert self.__x_prev is not None
        na = NoiseAnalysis(
            self._Components, self._NodeManager, self._config, self.__x_prev,
        )
        return na.analyze(
            f_start, f_stop, num_points,
            output_node_index=output_node_index,
            log_scale=log_scale,
        )

    def RunMonteCarlo(
        self,
        tolerances: list[tuple] | None = None,
        *,
        num_runs: int = 100,
        measure=None,
        seed: int | None = None,
    ):
        """
        Run a Monte Carlo analysis.

        Parameters
        ----------
        tolerances : list of (component, param_name, Tolerance)
            Each entry specifies a component, the parameter name
            (e.g. ``"Resistance"``), and a :class:`Tolerance`.
            If ``None``, use ``add_tolerance`` on the returned
            :class:`MonteCarlo` object instead.
        num_runs : int
            Number of random trials (default 100).
        measure : callable, optional
            ``measure(circuit, x_dc) -> float`` extracts the metric
            from each run.
        seed : int | None
            Random seed for reproducibility.

        Returns
        -------
        MonteCarloResult
        """
        from .MonteCarlo import MonteCarlo

        if not self._Finalized:
            raise RuntimeError("Circuit must be finalized first.")

        mc = MonteCarlo(self)
        if tolerances:
            for comp, param, tol in tolerances:
                mc.add_tolerance(comp, param, tol)
        return mc.run(num_runs, measure=measure, seed=seed)

    def RunSweep(
        self,
        parameters: list[tuple] | None = None,
        *,
        measure=None,
    ):
        """
        Run a parameter sweep.

        Parameters
        ----------
        parameters : list of (component, param_name, start, stop, num)
            or (component, param_name, values_list).
        measure : callable, optional
            ``measure(circuit, x_dc) -> float``.

        Returns
        -------
        SweepResult
        """
        from .ParameterSweep import ParameterSweep

        if not self._Finalized:
            raise RuntimeError("Circuit must be finalized first.")

        ps = ParameterSweep(self)
        if parameters:
            for entry in parameters:
                comp, param = entry[0], entry[1]
                rest = entry[2:]
                if len(rest) == 1 and hasattr(rest[0], '__iter__'):
                    ps.add_parameter_list(comp, param, rest[0])
                elif len(rest) == 3:
                    start, stop, num = rest
                    ps.add_parameter(comp, param,
                                     start=start, stop=stop, num=num)
                elif len(rest) == 2:
                    start, stop = rest
                    ps.add_parameter(comp, param, start=start, stop=stop)
                else:
                    raise ValueError(f"Bad sweep spec: {entry}")
        return ps.run(measure=measure)

    def RunHarmonicBalance(
        self,
        fundamental: float,
        *,
        num_harmonics: int = 7,
        max_iter: int = 200,
        tol: float = 1e-6,
    ):
        """
        Run a Harmonic Balance analysis.

        Finds the periodic steady state of a nonlinear circuit
        driven at *fundamental* Hz.

        Parameters
        ----------
        fundamental : float
            Fundamental frequency in Hz.
        num_harmonics : int
            Number of harmonics (default 7).
        max_iter : int
            Maximum Newton iterations.
        tol : float
            Convergence tolerance.

        Returns
        -------
        HBResult
        """
        from ..Solver.HarmonicBalance import HarmonicBalance

        if not self._Finalized:
            raise RuntimeError("Circuit must be finalized first.")
        if self.__x_prev is None:
            self.SolveDCOperatingPoint()

        assert self.__x_prev is not None
        hb = HarmonicBalance(
            self._Components, self._NodeManager, self._config, self.__x_prev,
        )
        return hb.solve(
            fundamental, num_harmonics=num_harmonics,
            max_iter=max_iter, tol=tol,
        )

    # ── simulation ──────────────────────────────────────────────────
    def Simulate(self, dt: float) -> np.ndarray:
        """
        Advance the simulation by one time-step of size *dt*.

        For **linear** circuits: single matrix build + solve.
        For **nonlinear** circuits: Newton-Raphson iteration until
        convergence, with damping and fallback strategies.

        Returns the solution vector ``x`` (node voltages followed by
        auxiliary unknowns).
        """
        if not self._Finalized:
            raise RuntimeError("Circuit must be finalized before simulation.")

        assert self._adaptive is not None
        assert self._system_builder is not None
        assert self._nr_solver is not None

        dt = self._adaptive.clamp(dt)
        self._ensure_initial_solution()
        ctx = self._prepare_context(dt)
        solution = self._solve_step(ctx)
        self._update_components(solution, ctx)
        self._check_energy()
        self._adaptive.update(dt, solution, ctx.x_prev)
        self._record(solution, dt)
        self._detect_events(solution, ctx)

        return solution

    # ── private simulation helpers ──────────────────────────────────
    def _ensure_initial_solution(self) -> None:
        """Compute DC operating point on first call if needed."""
        if self.__x_prev is None and not self.__dc_solved:
            if self._config.dc_operating_point:
                self.SolveDCOperatingPoint()
            else:
                n = self._NodeManager.TotalUnknownCount
                self.__x_prev = np.zeros(n)
                self.__dc_solved = True

    def _prepare_context(self, dt: float) -> SimulationContext:
        """Fill the reusable context with current step parameters."""
        ctx = self._context
        ctx.Mode = SimulationMode.TRANSIENT
        ctx.Time = self.__T
        ctx.dt = dt
        ctx.x_prev = self.__x_prev
        ctx.x_current = self.__x_prev
        ctx.integration_method = self._config.integration_method
        ctx.gmin = self._config.gmin
        ctx.source_factor = 1.0
        return ctx

    def _solve_step(self, ctx: SimulationContext) -> np.ndarray:
        """Run the linear or Newton-Raphson solver for one step."""
        assert self._nr_solver is not None
        assert self._system_builder is not None
        if self._has_nonlinear:
            return self._nr_solver.solve(ctx)
        A, b = self._system_builder.build(ctx)
        return self._Solver.Solve(A, b)

    def _update_components(self, solution: np.ndarray,
                           ctx: SimulationContext) -> None:
        """Push the new solution into every component's state."""
        for component in self._Components:
            component.UpdateState(solution, ctx)

    def _check_energy(self) -> None:
        """Periodic energy-conservation sanity check."""
        if (self._config.energy_check
                and self.__step_count % 100 == 0
                and self.__step_count > 0
                and self.__x_prev is not None):
            EnergyChecker.check(
                self._Components, self.__x_prev, self._config.max_energy,
            )

    def _record(self, solution: np.ndarray, dt: float) -> None:
        """Advance clock, store solution, and record probe data."""
        self.__x_prev = solution.copy()
        self.__T += dt
        self.__step_count += 1

        for probe in self._Probes:
            probe.Record(self.__T, solution)

    def _detect_events(self, solution: np.ndarray,
                       ctx: SimulationContext) -> None:
        """Run event detector if attached."""
        if self._event_detector is not None:
            self._event_detector.check(solution, self.__T, ctx)
