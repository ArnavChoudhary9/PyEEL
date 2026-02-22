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
        )

        x_dc = dc_solver.solve()
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

        # 1. Clamp dt
        dt = self._adaptive.clamp(dt)

        # 2. DC operating point on first call
        if self.__x_prev is None and not self.__dc_solved:
            if self._config.dc_operating_point:
                self.SolveDCOperatingPoint()
            else:
                n = self._NodeManager.TotalUnknownCount
                self.__x_prev = np.zeros(n)
                self.__dc_solved = True

        # 3. Prepare context
        ctx = self._context
        ctx.Mode = SimulationMode.TRANSIENT
        ctx.Time = self.__T
        ctx.dt = dt
        ctx.x_prev = self.__x_prev
        ctx.x_current = self.__x_prev
        ctx.integration_method = self._config.integration_method
        ctx.gmin = self._config.gmin
        ctx.source_factor = 1.0

        # 4. Solve
        if self._has_nonlinear:
            solution = self._nr_solver.solve(ctx)
        else:
            A, b = self._system_builder.build(ctx)
            solution = self._Solver.Solve(A, b)

        # 5. Update component state
        for component in self._Components:
            component.UpdateState(solution, ctx)

        # 6. Periodic energy sanity check
        if (self._config.energy_check
                and self.__step_count % 100 == 0
                and self.__step_count > 0):
            EnergyChecker.check(
                self._Components, solution, self._config.max_energy,
            )

        # 7. Adaptive timestep recommendation
        self._adaptive.update(dt, solution, ctx.x_prev)

        # 8. Record
        self.__x_prev = solution.copy()
        self.__T += dt
        self.__step_count += 1

        for probe in self._Probes:
            probe.Record(self.__T, solution)

        return solution
