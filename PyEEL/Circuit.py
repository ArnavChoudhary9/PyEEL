from __future__ import annotations

import logging
import numpy as np

from .Node import Node
from .NodeManager import NodeManager
from .SimulationContext import (
    SimulationContext, SimulationMode, SimulationConfig, IntegrationMethod,
)
from .Components.Component import Component
from .Solver.Solver import LinearSolver
from .Probe import Probe

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
    _Probes: list[Probe]
    _Solver: LinearSolver
    _Finalized: bool
    _config: SimulationConfig

    __T: float
    __x_prev: np.ndarray | None
    __dc_solved: bool
    __step_count: int
    _recommended_dt: float | None

    def __init__(self, solver: LinearSolver,
                 config: SimulationConfig | None = None):
        self._NodeManager = NodeManager()
        self._Components = []
        self._Probes = []
        self._Solver = solver
        self._Finalized = False
        self._config = config if config is not None else SimulationConfig()

        self.__T = 0.0
        self.__x_prev = None
        self.__dc_solved = False
        self.__step_count = 0
        self._recommended_dt = None

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
    def Probes(self) -> list[Probe]:
        """All measurement probes attached to this circuit."""
        return self._Probes

    @property
    def Config(self) -> SimulationConfig:
        """Simulation configuration (read-only reference)."""
        return self._config

    @property
    def RecommendedDt(self) -> float | None:
        """Recommended dt from adaptive timestep heuristic (``None`` if disabled)."""
        return self._recommended_dt

    # ── setup ───────────────────────────────────────────────────────
    def Reset(self) -> None:
        """Reset the simulation clock, previous solution, and all probes."""
        self.__T = 0.0
        self.__x_prev = None
        self.__dc_solved = False
        self.__step_count = 0
        self._recommended_dt = None

        for probe in self._Probes:
            probe.Clear()

    def AddComponent(self, component: Component) -> None:
        """Add a component **before** :meth:`Finalize` is called."""
        if self._Finalized:
            raise RuntimeError("Cannot add component to a finalized circuit.")
        self._Components.append(component)

    def AddProbe(self, probe: Probe) -> None:
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

        # Pre-allocate MNA system arrays (zeroed in-place each step)
        n = self._NodeManager.TotalUnknownCount
        self._A = np.zeros((n, n))
        self._b = np.zeros(n)

        # Reusable simulation context (mutated each step to avoid
        # repeated dataclass construction overhead)
        self._context = SimulationContext(
            Mode=SimulationMode.TRANSIENT, Time=0.0, dt=0.0,
            integration_method=self._config.integration_method,
            gmin=self._config.gmin,
        )

        # ── topology sanity checks ─────────────────────────────────
        self._validate_topology()

    # ── topology validation ───────────────────────────────────────────
    def _validate_topology(self) -> None:
        """
        Check the circuit for common topology problems that would lead
        to singular matrices or non-physical results.

        Logs warnings (does not raise) so the simulation can still
        attempt to run — Gmin may save a marginally-bad topology.
        """
        from .Components.Capacitor import Capacitor
        from .Components.Inductor import Inductor
        from .Components.Sources.VoltageSource import VoltageSource

        nv = self._NodeManager.VoltageUnknownCount

        # ── 1. Check every node is connected to at least one component ──
        node_component_count: dict[int, list[Component]] = {
            i: [] for i in range(nv)
        }
        for comp in self._Components:
            for node in comp.Nodes:
                if node.Index is not None and node.Index < nv:
                    node_component_count[node.Index].append(comp)

        for idx, comps in node_component_count.items():
            if not comps:
                node_name = self._find_node_name(idx)
                logger.warning(
                    "Node '%s' (index %d) is not connected to any component. "
                    "This will cause a singular matrix.",
                    node_name, idx,
                )

        # ── 2. Warn about nodes connected *only* through capacitors ──
        for idx, comps in node_component_count.items():
            if comps and all(isinstance(c, Capacitor) for c in comps):
                node_name = self._find_node_name(idx)
                logger.warning(
                    "Node '%s' is only connected through capacitors "
                    "(DC-floating). Gmin will stabilise it, but this "
                    "may indicate a topology error.",
                    node_name,
                )

        # ── 3. Check for voltage-source loops ──────────────────────
        #       (Two voltage sources sharing the same two nodes with
        #        different values create a contradictory KVL.)
        vs_pairs: dict[tuple[int | None, int | None], list[str]] = {}
        for comp in self._Components:
            if isinstance(comp, VoltageSource):
                n1_idx = comp.Nodes[0].Index
                n2_idx = comp.Nodes[1].Index
                key = (min(n1_idx or -1, n2_idx or -1),
                       max(n1_idx or -1, n2_idx or -1))
                vs_pairs.setdefault(key, []).append(comp.Name)
        for key, names in vs_pairs.items():
            if len(names) > 1:
                logger.warning(
                    "Voltage sources %s share the same node pair — "
                    "this creates conflicting KVL constraints and "
                    "will likely produce a singular matrix.",
                    names,
                )

        # ── 4. Warn about extreme component values ─────────────────
        from .Components.Resistor import Resistor

        for comp in self._Components:
            if isinstance(comp, Resistor):
                if comp.Resistance > 1e15 or comp.Resistance < 1e-15:
                    logger.warning(
                        "Resistor '%s' has extreme value %.2e Ω — "
                        "consider rescaling for better conditioning.",
                        comp.Name, comp.Resistance,
                    )
            elif isinstance(comp, Capacitor):
                if comp.Capacitance > 1e6 or comp.Capacitance < 1e-18:
                    logger.warning(
                        "Capacitor '%s' has extreme value %.2e F — "
                        "consider rescaling for better conditioning.",
                        comp.Name, comp.Capacitance,
                    )
            elif isinstance(comp, Inductor):
                if comp.Inductance > 1e6 or comp.Inductance < 1e-18:
                    logger.warning(
                        "Inductor '%s' has extreme value %.2e H — "
                        "consider rescaling for better conditioning.",
                        comp.Name, comp.Inductance,
                    )

    def _find_node_name(self, index: int) -> str:
        """Return the human-readable name of the node with *index*."""
        for name, node in self._NodeManager._Nodes.items():
            if node.Index == index:
                return name
        return f"<index {index}>"

    # ── Gmin stamp ──────────────────────────────────────────────────
    def _stamp_gmin(self, A: np.ndarray) -> None:
        """
        Add a small conductance ``Gmin`` from every voltage node to
        ground.  This prevents singular matrices caused by floating
        nodes or pure-capacitor cutsets.
        """
        gmin = self._config.gmin
        nv = self._NodeManager.VoltageUnknownCount
        for i in range(nv):
            A[i, i] += gmin

    # ── dt clamping ─────────────────────────────────────────────────
    def _clamp_dt(self, dt: float) -> float:
        """Clamp *dt* to the configured ``[min_dt, max_dt]`` range."""
        return max(self._config.min_dt, min(dt, self._config.max_dt))

    # ── DC operating point ──────────────────────────────────────────
    def SolveDCOperatingPoint(self) -> np.ndarray:
        """
        Solve the DC operating point and store the result as the
        initial condition (``x_prev``) for the transient simulation.

        * Capacitors → open circuit (no stamp).
        * Inductors  → short circuit (large conductance).
        * Coupling   → inactive.
        * Sources    → evaluate their DC component.

        Returns the DC solution vector.
        """
        if not self._Finalized:
            raise RuntimeError("Circuit must be finalized first.")

        n = self._NodeManager.TotalUnknownCount
        A_dc = np.zeros((n, n))
        b_dc = np.zeros(n)

        dc_context = SimulationContext(
            Mode=SimulationMode.DC,
            Time=0.0,
            dt=0.0,     # not used in DC
            x_prev=None,
            integration_method=self._config.integration_method,
            gmin=self._config.gmin,
        )

        for comp in self._Components:
            comp.Stamp(A_dc, b_dc, dc_context)

        # Gmin on every voltage node
        gmin = self._config.gmin
        nv = self._NodeManager.VoltageUnknownCount
        for i in range(nv):
            A_dc[i, i] += gmin

        try:
            x_dc = self._Solver.Solve(A_dc, b_dc)
            self.__x_prev = x_dc.copy()
            self.__dc_solved = True

            # Propagate the DC solution into component states
            for comp in self._Components:
                comp.UpdateState(x_dc, dc_context)

            logger.info("DC operating point solved successfully.")
            return x_dc

        except Exception as exc:
            logger.warning(
                "DC operating point solve failed (%s). "
                "Starting transient from zero initial conditions.",
                exc,
            )
            self.__x_prev = np.zeros(n)
            self.__dc_solved = True
            return self.__x_prev

    # ── energy sanity check ─────────────────────────────────────────
    def _check_energy(self, solution: np.ndarray) -> None:
        """
        Verify that energy stored in reactive components has not
        exploded to non-physical levels.  Logs a warning when a
        threshold is exceeded.
        """
        from .Components.Capacitor import Capacitor
        from .Components.Inductor import Inductor

        max_energy = self._config.max_energy

        for comp in self._Components:
            if isinstance(comp, Capacitor):
                v = comp.GetVoltage(solution)
                energy = 0.5 * comp.Capacitance * v * v
                if energy > max_energy:
                    logger.warning(
                        "Capacitor '%s': energy = %.2e J exceeds "
                        "threshold %.2e J — possible instability.",
                        comp.Name, energy, max_energy,
                    )
            elif isinstance(comp, Inductor):
                i = comp._current
                energy = 0.5 * comp.Inductance * i * i
                if energy > max_energy:
                    logger.warning(
                        "Inductor '%s': energy = %.2e J exceeds "
                        "threshold %.2e J — possible instability.",
                        comp.Name, energy, max_energy,
                    )

    # ── adaptive timestep heuristic ─────────────────────────────────
    def _update_recommended_dt(self, dt: float,
                               solution: np.ndarray,
                               x_prev: np.ndarray | None) -> None:
        """Compute a recommended dt for the next step."""
        if not self._config.adaptive_timestep or x_prev is None:
            self._recommended_dt = dt
            return

        dx_max = float(np.max(np.abs(solution - x_prev)))
        x_scale = max(float(np.max(np.abs(solution))), 1.0)
        relative_change = dx_max / x_scale

        cfg = self._config
        if relative_change > cfg.adaptive_threshold:
            self._recommended_dt = max(dt * cfg.adaptive_shrink,
                                       cfg.min_dt)
        elif relative_change < cfg.adaptive_threshold * 0.1:
            grow = min(cfg.adaptive_grow, cfg.max_grow_factor)
            self._recommended_dt = min(dt * grow, cfg.max_dt)
        else:
            self._recommended_dt = dt

    # ── simulation ──────────────────────────────────────────────────
    def _BuildSystem(self, context: SimulationContext) -> tuple:
        """Assemble the global MNA matrix **A** and vector **b**."""
        self._A[:] = 0.0       # zero in-place — no allocation
        self._b[:] = 0.0

        for component in self._Components:
            component.Stamp(self._A, self._b, context)

        # Global Gmin: small conductance from every voltage node to GND
        self._stamp_gmin(self._A)

        return self._A, self._b

    def Simulate(self, dt: float) -> np.ndarray:
        """
        Advance the simulation by one time-step of size *dt*.

        Steps performed:

        1. Clamp *dt* to ``[min_dt, max_dt]``.
        2. Solve DC operating point on the very first call (if enabled).
        3. Build the MNA system (components + Gmin).
        4. Solve ``A x = b`` (LAPACK with partial pivoting).
        5. Update component states **only after** a successful solve.
        6. Periodic energy sanity check.
        7. Compute recommended dt (adaptive heuristic, if enabled).
        8. Record probe data.

        Returns the solution vector ``x`` (node voltages followed by
        auxiliary unknowns).
        """
        if not self._Finalized:
            raise RuntimeError("Circuit must be finalized before simulation.")

        # ── 1. clamp dt ────────────────────────────────────────────
        dt = self._clamp_dt(dt)

        # ── 2. DC operating point on first call ────────────────────
        if self.__x_prev is None and not self.__dc_solved:
            if self._config.dc_operating_point:
                self.SolveDCOperatingPoint()
            else:
                n = self._NodeManager.TotalUnknownCount
                self.__x_prev = np.zeros(n)
                self.__dc_solved = True

        # ── 3 + 4. build & solve ───────────────────────────────────
        context = self._context
        context.Mode = SimulationMode.TRANSIENT
        context.Time = self.__T
        context.dt = dt
        context.x_prev = self.__x_prev
        context.integration_method = self._config.integration_method
        context.gmin = self._config.gmin

        A, b = self._BuildSystem(context)
        solution = self._Solver.Solve(A, b)

        # ── 5. update state after successful solve only ─────────────
        for component in self._Components:
            component.UpdateState(solution, context)

        # ── 6. periodic energy sanity check ─────────────────────────
        if (self._config.energy_check
                and self.__step_count % 100 == 0
                and self.__step_count > 0):
            self._check_energy(solution)

        # ── 7. adaptive timestep recommendation ─────────────────────
        self._update_recommended_dt(dt, solution, context.x_prev)

        # ── 8. record ──────────────────────────────────────────────
        self.__x_prev = solution.copy()
        self.__T += dt
        self.__step_count += 1

        for probe in self._Probes:
            probe.Record(self.__T, solution)

        return solution
