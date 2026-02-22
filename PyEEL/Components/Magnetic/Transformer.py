"""
Ideal two-winding transformer built from two inductors and a
:class:`MutualCoupling`.

This is a convenience component: it internally creates an
:class:`Inductor` for each winding and a :class:`MutualCoupling`
that links them, then delegates every MNA call to those three
sub-components.
"""

from __future__ import annotations

import numpy as np

from ...Core.Node import Node
from ...Core.NodeManager import NodeManager
from ...Core.SimulationContext import SimulationContext
from ..Component import Component
from ..Passive.Inductor import Inductor
from .MutualCoupling import MutualCoupling


class Transformer(Component):
    """
    Ideal two-winding transformer.

    Parameters
    ----------
    name : str
        Component identifier (e.g. ``'T1'``).
    primary_nodes : tuple[Node, Node]
        ``(positive, negative)`` terminals of the primary winding.
    secondary_nodes : tuple[Node, Node]
        ``(positive, negative)`` terminals of the secondary winding.
    primary_inductance : float
        Primary winding inductance (H).
    secondary_inductance : float
        Secondary winding inductance (H).
    k : float
        Coupling coefficient (``|k| < 1``).
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
        all_nodes = list(primary_nodes) + list(secondary_nodes)
        unique_nodes = tuple(dict.fromkeys(all_nodes))
        super().__init__(name, unique_nodes)

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
        return self._primary

    @property
    def Secondary(self) -> Inductor:
        return self._secondary

    @property
    def Coupling(self) -> MutualCoupling:
        return self._coupling

    @property
    def TurnsRatio(self) -> float:
        return (self._primary.Inductance / self._secondary.Inductance) ** 0.5

    @property
    def MutualInductance(self) -> float:
        return self._coupling.MutualInductance

    @property
    def CouplingCoefficient(self) -> float:
        return self._coupling.CouplingCoefficient

    # ── MNA interface (delegated) ───────────────────────────────────
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
        return self._primary.GetCurrent(solutionVector)

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        return self._primary.GetVoltage(solutionVector)

    def GetSecondaryCurrent(self, solutionVector: np.ndarray) -> float:
        return self._secondary.GetCurrent(solutionVector)

    def GetSecondaryVoltage(self, solutionVector: np.ndarray) -> float:
        return self._secondary.GetVoltage(solutionVector)
