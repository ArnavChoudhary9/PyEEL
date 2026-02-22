"""
MNA system builder — assembles the global matrix ``A`` and vector ``b``
from component stamps.

This class owns the pre-allocated NumPy arrays and provides a single
``build(context)`` call that zeros them, iterates over all components,
and applies the global Gmin conductance.
"""

from __future__ import annotations

import numpy as np

from ..Core.NodeManager import NodeManager
from ..Core.SimulationContext import SimulationContext
from ..Components.Component import Component


class MNASystemBuilder:
    """
    Assembles the MNA matrix and RHS vector from component stamps.

    Parameters
    ----------
    components : list[Component]
        All circuit components.
    node_manager : NodeManager
        Manages node indices.
    gmin : float
        Default Gmin conductance to stamp on every voltage node.
    """

    def __init__(self, components: list[Component],
                 node_manager: NodeManager,
                 gmin: float = 1e-12):
        self._components = components
        self._node_manager = node_manager
        self._gmin = gmin

        n = node_manager.TotalUnknownCount
        self._A = np.zeros((n, n))
        self._b = np.zeros(n)

    @property
    def gmin(self) -> float:
        return self._gmin

    @gmin.setter
    def gmin(self, value: float) -> None:
        self._gmin = value

    def build(self, context: SimulationContext) -> tuple[np.ndarray, np.ndarray]:
        """
        Zero, stamp all components, apply Gmin, and return ``(A, b)``.

        The returned arrays are the *same* pre-allocated objects — do
        not hold references across calls.
        """
        self._A[:] = 0.0
        self._b[:] = 0.0

        for component in self._components:
            component.Stamp(self._A, self._b, context)

        # Gmin: small conductance from every voltage node to ground
        gmin = self._gmin
        nv = self._node_manager.VoltageUnknownCount
        for i in range(nv):
            self._A[i, i] += gmin

        return self._A, self._b
