from .Node import Node
from .NodeManager import NodeManager
from .SimulationContext import SimulationContext, SimulationMode
from .Components.Component import Component
from .Solver.Solver import LinearSolver
from .Probe import Probe

import numpy as np


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

    __T: float
    __x_prev: np.ndarray | None

    def __init__(self, solver: LinearSolver):
        self._NodeManager = NodeManager()
        self._Components = []
        self._Probes = []
        self._Solver = solver
        self._Finalized = False

        self.__T = 0.0
        self.__x_prev = None

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

    # ── setup ───────────────────────────────────────────────────────
    def Reset(self) -> None:
        """Reset the simulation clock, previous solution, and all probes."""
        self.__T = 0.0
        self.__x_prev = None

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
        Freeze the topology and let every component register its
        auxiliary unknowns.  Must be called exactly once before
        :meth:`Simulate`.
        """
        if self._Finalized:
            raise RuntimeError("Circuit is already finalized.")

        self._NodeManager.Freeze()

        for component in self._Components:
            component.RegisterUnknowns(self._NodeManager)

        self._Finalized = True

    # ── simulation ──────────────────────────────────────────────────
    def _BuildSystem(self, context: SimulationContext) -> tuple:
        """Assemble the global MNA matrix **A** and vector **b**."""
        n = self._NodeManager.TotalUnknownCount
        A = np.zeros((n, n))
        b = np.zeros(n)

        for component in self._Components:
            component.Stamp(A, b, context)

        return A, b

    def Simulate(self, dt: float) -> np.ndarray:
        """
        Advance the simulation by one time-step of size *dt*.

        Returns the solution vector ``x`` (node voltages followed by
        auxiliary unknowns).
        """
        if not self._Finalized:
            raise RuntimeError("Circuit must be finalized before simulation.")

        context = SimulationContext(
            Mode=SimulationMode.TRANSIENT,
            Time=self.__T,
            dt=dt,
            x_prev=self.__x_prev,
        )

        A, b = self._BuildSystem(context)
        solution = self._Solver.Solve(A, b)

        for component in self._Components:
            component.UpdateState(solution, context)

        self.__x_prev = solution
        self.__T += dt

        # Record data for all attached probes
        for probe in self._Probes:
            probe.Record(self.__T, solution)

        return solution
