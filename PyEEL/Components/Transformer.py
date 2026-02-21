from __future__ import annotations

from ..Node import Node
from ..NodeManager import NodeManager
from ..SimulationContext import SimulationContext
from .Component import Component
from .Inductor import Inductor
from .MutualCoupling import MutualCoupling

import numpy as np


class Transformer(Component):
    """
    Ideal two-winding transformer built from two inductors and a
    :class:`MutualCoupling`.

    This is a convenience component: it internally creates an
    :class:`Inductor` for each winding and a :class:`MutualCoupling`
    that links them, then delegates every MNA call to those three
    sub-components.

    Topology::

        primary_p ──┤ L1 (primary) ├── primary_n
        secondary_p ──┤ L2 (secondary) ├── secondary_n

        K couples L1 ↔ L2 with coefficient *k*.

    Parameters
    ----------
    name : str
        Component identifier (e.g. ``'T1'``).
    primary_nodes : tuple[Node, Node]
        ``(positive, negative)`` terminals of the primary winding.
    secondary_nodes : tuple[Node, Node]
        ``(positive, negative)`` terminals of the secondary winding.
    primary_inductance : float
        Inductance of the primary winding in henrys (H).
    secondary_inductance : float
        Inductance of the secondary winding in henrys (H).
    k : float
        Coupling coefficient (``|k| < 1``).  Positive for aiding,
        negative for opposing coupling.

    Attributes
    ----------
    Primary : Inductor
        The primary-winding inductor (use for current probes, etc.).
    Secondary : Inductor
        The secondary-winding inductor.
    Coupling : MutualCoupling
        The internal coupling element.
    """

    _primary: Inductor
    _secondary: Inductor
    _coupling: MutualCoupling

    def __init__(
        self,
        name: str,
        primary_nodes: tuple[Node, Node],
        secondary_nodes: tuple[Node, Node],
        primary_inductance: float,
        secondary_inductance: float,
        k: float,
    ):
        # Collect unique nodes across both windings for the base class.
        all_nodes = list(primary_nodes) + list(secondary_nodes)
        unique_nodes = tuple(dict.fromkeys(all_nodes))
        super().__init__(name, unique_nodes)

        # ── internal sub-components ─────────────────────────────────
        self._primary = Inductor(
            f"{name}.L1", primary_nodes, primary_inductance
        )
        self._secondary = Inductor(
            f"{name}.L2", secondary_nodes, secondary_inductance
        )
        self._coupling = MutualCoupling(
            f"{name}.K", self._primary, self._secondary, k
        )

    # ── properties ──────────────────────────────────────────────────
    @property
    def Primary(self) -> Inductor:
        """Primary-winding inductor."""
        return self._primary

    @property
    def Secondary(self) -> Inductor:
        """Secondary-winding inductor."""
        return self._secondary

    @property
    def Coupling(self) -> MutualCoupling:
        """Internal :class:`MutualCoupling` element."""
        return self._coupling

    @property
    def TurnsRatio(self) -> float:
        """Effective turns ratio ``n = √(L1 / L2)``."""
        return (self._primary.Inductance / self._secondary.Inductance) ** 0.5

    @property
    def MutualInductance(self) -> float:
        """Mutual inductance *M* in henrys (H)."""
        return self._coupling.MutualInductance

    @property
    def CouplingCoefficient(self) -> float:
        """Coupling coefficient *k* (dimensionless)."""
        return self._coupling.CouplingCoefficient

    # ── MNA interface (delegated to sub-components) ─────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        self._primary.RegisterUnknowns(nodeManager)
        self._secondary.RegisterUnknowns(nodeManager)
        self._coupling.RegisterUnknowns(nodeManager)

    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        self._primary.Stamp(A, b, context)
        self._secondary.Stamp(A, b, context)
        self._coupling.Stamp(A, b, context)

    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        self._primary.UpdateState(solutionVector, context)
        self._secondary.UpdateState(solutionVector, context)
        self._coupling.UpdateState(solutionVector, context)

    # ── query helpers ───────────────────────────────────────────────
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """Return the primary winding current."""
        return self._primary.GetCurrent(solutionVector)

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return the primary winding voltage."""
        return self._primary.GetVoltage(solutionVector)

    def GetSecondaryCurrent(self, solutionVector: np.ndarray) -> float:
        """Return the secondary winding current."""
        return self._secondary.GetCurrent(solutionVector)

    def GetSecondaryVoltage(self, solutionVector: np.ndarray) -> float:
        """Return the secondary winding voltage."""
        return self._secondary.GetVoltage(solutionVector)
