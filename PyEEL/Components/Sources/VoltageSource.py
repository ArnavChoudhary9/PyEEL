from .Source import Source
from .Waveform import Waveform, ConstantWave, SineWave
from ...Node import Node
from ...NodeManager import NodeManager
from ...SimulationContext import SimulationContext

import numpy as np


class VoltageSource(Source):
    """
    Ideal independent voltage source.

    Forces ``V(n1) - V(n2) = v(t)`` by introducing an auxiliary unknown
    for the branch current and adding the corresponding KVL row to the
    MNA system.
    """

    def __init__(self, name: str, nodes: tuple[Node, Node], waveform: Waveform):
        super().__init__(name, nodes, waveform)

    # ── MNA interface ───────────────────────────────────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        """Request one auxiliary unknown for the branch current."""
        self._aux_indices.append(nodeManager.RequestAuxiliaryUnknown())

    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        """
        Stamp the voltage-source constraint into the MNA system.

        Adds the KVL equation ``V(n1) - V(n2) = v(t)`` via an auxiliary
        row/column, properly handling the case where either terminal is
        the ground node (``Index is None``).
        """
        n1, n2 = self.Nodes
        aux = self.AuxIndices[0]

        if n1.Index is not None:
            A[aux, n1.Index] = 1
            A[n1.Index, aux] = 1

        if n2.Index is not None:
            A[aux, n2.Index] = -1
            A[n2.Index, aux] = -1

        b[aux] = self.EvaluateWaveform(context)

    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        """Ideal voltage sources are memoryless — nothing to update."""
        pass

    # ── query helpers ───────────────────────────────────────────────
    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """Return the branch current (stored as the auxiliary unknown)."""
        return float(solutionVector[self.AuxIndices[0]])

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return ``V(n1) - V(n2)``."""
        n1, n2 = self.Nodes
        v1 = solutionVector[n1.Index] if n1.Index is not None else 0.0
        v2 = solutionVector[n2.Index] if n2.Index is not None else 0.0
        return float(v1 - v2)


# ── convenience factories ───────────────────────────────────────────
def DCVoltageSource(name: str, nodes: tuple[Node, Node],
                    voltage: float) -> VoltageSource:
    """Create a constant (DC) voltage source."""
    return VoltageSource(name, nodes, ConstantWave(voltage))


def ACVoltageSource(name: str, nodes: tuple[Node, Node],
                    amplitude: float, frequency: float) -> VoltageSource:
    """Create a sinusoidal (AC) voltage source."""
    return VoltageSource(name, nodes, SineWave(frequency, amplitude))
