from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ..Core.Node import Node
from ..Core.NodeManager import NodeManager
from ..Core.SimulationContext import SimulationContext


class Component(ABC):
    """
    Abstract base class for every circuit component.

    A component connects two or more :class:`Node` objects and knows how
    to contribute its constitutive equations to the global MNA system via
    the :meth:`Stamp` method.

    Convention: current flows from ``Nodes[0]`` toward ``Nodes[1]``.
    """

    _Name: str
    _Nodes: tuple[Node, ...]
    _aux_indices: list[int]
    _state: dict[str, float]

    def __init__(self, name: str, nodes: tuple[Node, ...],
                 aux_indices: list[int] | None = None):
        self._Name = name
        self._Nodes = nodes
        # Avoid the mutable-default-argument pitfall
        self._aux_indices = aux_indices if aux_indices is not None else []
        self._state = {}

        if not nodes:
            raise ValueError(f"Component {name} must have at least one node.")
        if len(set(nodes)) != len(nodes):
            raise ValueError(f"Component {name} has duplicate nodes.")

    # ── properties ──────────────────────────────────────────────────
    @property
    def Name(self) -> str:
        """Component identifier (e.g. ``'R1'``, ``'VS1'``)."""
        return self._Name

    @property
    def Nodes(self) -> tuple[Node, ...]:
        """Tuple of nodes this component is connected to."""
        return self._Nodes

    @property
    def AuxIndices(self) -> list[int]:
        """Indices of auxiliary unknowns owned by this component."""
        return self._aux_indices

    @property
    def PreviousState(self) -> dict[str, float]:
        """State dictionary preserved across simulation steps."""
        return self._state

    @property
    def IsNonlinear(self) -> bool:
        """``True`` if this component requires Newton-Raphson iteration.

        Linear components (default) return ``False``.  Nonlinear
        subclasses (diodes, BJTs, …) override this to ``True``.
        """
        return False

    # ── abstract interface ──────────────────────────────────────────
    @abstractmethod
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        """Request any auxiliary unknowns from the *nodeManager*."""
        ...

    @abstractmethod
    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        """
        Add this component's contribution to the MNA matrix **A**
        and excitation vector **b**.
        """
        ...

    @abstractmethod
    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        """Update internal state after solving the current time-step."""
        ...

    @abstractmethod
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """Return current through this component (A)."""
        ...

    @abstractmethod
    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return voltage across this component (V)."""
        ...
