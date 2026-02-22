"""
Dependent (controlled) sources for MNA-based circuit simulation.

This module provides all four linear dependent sources used in
circuit analysis:

=====  ====================================  ===================
SPICE  Description                           Controlling quantity
=====  ====================================  ===================
**E**  Voltage-Controlled Voltage Source      Voltage
**G**  Voltage-Controlled Current Source      Voltage
**H**  Current-Controlled Voltage Source      Current
**F**  Current-Controlled Current Source      Current
=====  ====================================  ===================

MNA formulations
----------------

**VCVS** (E-source)::

    V(out+) − V(out−) = μ · [V(ctrl+) − V(ctrl−)]

    Introduces one auxiliary unknown (output branch current ``I_E``).
    KVL row:  V(out+) − V(out−) − μ·V(ctrl+) + μ·V(ctrl−) = 0

**VCCS** (G-source)::

    I_out = g · [V(ctrl+) − V(ctrl−)]

    No auxiliary unknowns — stamps as a transconductance matrix.

**CCVS** (H-source)::

    V(out+) − V(out−) = r · I_ctrl

    The controlling current ``I_ctrl`` must flow through
    a zero-volt voltage source (sense element).  Two auxiliary
    unknowns: ``I_sense`` (controlling branch) and ``I_H``
    (output branch).

**CCCS** (F-source)::

    I_out = α · I_ctrl

    The controlling current ``I_ctrl`` flows through a zero-volt
    sense element.  One auxiliary unknown: ``I_sense``.

Conventions
-----------
* ``(out_pos, out_neg)`` — output terminal pair; current exits
  ``out_pos``.
* ``(ctrl_pos, ctrl_neg)`` — controlling terminal pair; the
  controlling voltage is ``V(ctrl_pos) − V(ctrl_neg)``.
* For current-controlled sources, the controlling current is
  defined as flowing **into** ``ctrl_pos`` through a zero-volt
  sense element.
"""

from __future__ import annotations

import numpy as np

from ...Core.Node import Node
from ...Core.NodeManager import NodeManager
from ...Core.SimulationContext import SimulationContext
from ..Component import Component


# ════════════════════════════════════════════════════════════════════
#  VCVS — Voltage-Controlled Voltage Source  (E)
# ════════════════════════════════════════════════════════════════════

class VCVS(Component):
    """
    Voltage-Controlled Voltage Source (E-source).

    ``V(out+) − V(out−) = μ · [V(ctrl+) − V(ctrl−)]``

    Parameters
    ----------
    name : str
        Component identifier (e.g. ``'E1'``).
    out_nodes : tuple[Node, Node]
        ``(out+, out−)`` — output terminal pair.
    ctrl_nodes : tuple[Node, Node]
        ``(ctrl+, ctrl−)`` — controlling voltage sensing nodes.
    gain : float
        Voltage gain ``μ`` (V/V).  Dimensionless.
    """

    _ctrl_nodes: tuple[Node, Node]
    _gain: float

    def __init__(self, name: str,
                 out_nodes: tuple[Node, Node],
                 ctrl_nodes: tuple[Node, Node],
                 gain: float):
        # The Component base class stores out_nodes as self.Nodes
        super().__init__(name, out_nodes)
        self._ctrl_nodes = ctrl_nodes
        self._gain = gain

    @property
    def Gain(self) -> float:
        return self._gain

    @property
    def ControlNodes(self) -> tuple[Node, Node]:
        return self._ctrl_nodes

    # ── MNA interface ───────────────────────────────────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        """One auxiliary unknown for the output branch current."""
        self._aux_indices.append(nodeManager.RequestAuxiliaryUnknown())

    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        """
        Stamp the VCVS into the MNA system.

        Auxiliary row (KVL)::

            V(out+) − V(out−) − μ·V(ctrl+) + μ·V(ctrl−) = 0

        The branch current ``I_E`` appears in the KCL equations of
        ``out+`` (enters) and ``out−`` (leaves).
        """
        op = self.Nodes[0].Index     # out+
        om = self.Nodes[1].Index     # out-
        cp = self._ctrl_nodes[0].Index  # ctrl+
        cm = self._ctrl_nodes[1].Index  # ctrl-
        aux = self.AuxIndices[0]     # branch current I_E
        mu = self._gain

        # KCL: branch current into out+, out of out-
        if op is not None:
            A[op, aux] += 1
            A[aux, op] += 1
        if om is not None:
            A[om, aux] -= 1
            A[aux, om] -= 1

        # KVL: −μ·V(ctrl+) + μ·V(ctrl−)
        if cp is not None:
            A[aux, cp] -= mu
        if cm is not None:
            A[aux, cm] += mu

        # b[aux] = 0  (no independent source term)

    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        pass

    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """Return the output branch current ``I_E``."""
        return float(solutionVector[self.AuxIndices[0]])

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return ``V(out+) − V(out−)``."""
        op, om = self.Nodes
        v1 = float(solutionVector[op.Index]) if op.Index is not None else 0.0
        v2 = float(solutionVector[om.Index]) if om.Index is not None else 0.0
        return v1 - v2


# ════════════════════════════════════════════════════════════════════
#  VCCS — Voltage-Controlled Current Source  (G)
# ════════════════════════════════════════════════════════════════════

class VCCS(Component):
    """
    Voltage-Controlled Current Source (G-source).

    ``I_out = g · [V(ctrl+) − V(ctrl−)]``

    Current flows from ``out+`` to ``out−`` (exits ``out+``).

    Parameters
    ----------
    name : str
        Component identifier (e.g. ``'G1'``).
    out_nodes : tuple[Node, Node]
        ``(out+, out−)`` — output terminal pair.
    ctrl_nodes : tuple[Node, Node]
        ``(ctrl+, ctrl−)`` — controlling voltage sensing nodes.
    transconductance : float
        Transconductance ``g`` (A/V, i.e. siemens).
    """

    _ctrl_nodes: tuple[Node, Node]
    _gm: float
    _current: float

    def __init__(self, name: str,
                 out_nodes: tuple[Node, Node],
                 ctrl_nodes: tuple[Node, Node],
                 transconductance: float):
        super().__init__(name, out_nodes)
        self._ctrl_nodes = ctrl_nodes
        self._gm = transconductance
        self._current = 0.0

    @property
    def Transconductance(self) -> float:
        return self._gm

    @property
    def ControlNodes(self) -> tuple[Node, Node]:
        return self._ctrl_nodes

    # ── MNA interface ───────────────────────────────────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        """VCCS introduces no auxiliary unknowns."""
        pass

    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        """
        Stamp the VCCS transconductance into the MNA system.

        The output current ``I = g·(V_cp − V_cm)`` enters ``out+``
        and leaves ``out−``.

        Conductance-matrix stamps::

            A[out+, ctrl+] += g    A[out+, ctrl−] −= g
            A[out−, ctrl+] −= g    A[out−, ctrl−] += g
        """
        op = self.Nodes[0].Index
        om = self.Nodes[1].Index
        cp = self._ctrl_nodes[0].Index
        cm = self._ctrl_nodes[1].Index
        g = self._gm

        if op is not None:
            if cp is not None:
                A[op, cp] += g
            if cm is not None:
                A[op, cm] -= g
        if om is not None:
            if cp is not None:
                A[om, cp] -= g
            if cm is not None:
                A[om, cm] += g

    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        # Compute the output current for GetCurrent
        cp = self._ctrl_nodes[0].Index
        cm = self._ctrl_nodes[1].Index
        vc_p = float(solutionVector[cp]) if cp is not None else 0.0
        vc_m = float(solutionVector[cm]) if cm is not None else 0.0
        self._current = self._gm * (vc_p - vc_m)

    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """Return the output current ``I = g · V_ctrl``."""
        return self._current

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return ``V(out+) − V(out−)``."""
        op, om = self.Nodes
        v1 = float(solutionVector[op.Index]) if op.Index is not None else 0.0
        v2 = float(solutionVector[om.Index]) if om.Index is not None else 0.0
        return v1 - v2


# ════════════════════════════════════════════════════════════════════
#  CCVS — Current-Controlled Voltage Source  (H)
# ════════════════════════════════════════════════════════════════════

class CCVS(Component):
    """
    Current-Controlled Voltage Source (H-source).

    ``V(out+) − V(out−) = r · I_ctrl``

    The controlling current ``I_ctrl`` is sensed by inserting a
    zero-volt voltage source between ``ctrl+`` and ``ctrl−``
    (current flows from ``ctrl+`` to ``ctrl−``).

    Parameters
    ----------
    name : str
        Component identifier (e.g. ``'H1'``).
    out_nodes : tuple[Node, Node]
        ``(out+, out−)`` — output terminal pair.
    ctrl_nodes : tuple[Node, Node]
        ``(ctrl+, ctrl−)`` — controlling current sensing terminals.
        A zero-volt source is inserted between them.
    transresistance : float
        Transresistance ``r`` (V/A, i.e. ohms).
    """

    _ctrl_nodes: tuple[Node, Node]
    _rm: float

    def __init__(self, name: str,
                 out_nodes: tuple[Node, Node],
                 ctrl_nodes: tuple[Node, Node],
                 transresistance: float):
        super().__init__(name, out_nodes)
        self._ctrl_nodes = ctrl_nodes
        self._rm = transresistance

    @property
    def Transresistance(self) -> float:
        return self._rm

    @property
    def ControlNodes(self) -> tuple[Node, Node]:
        return self._ctrl_nodes

    # ── MNA interface ───────────────────────────────────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        """
        Two auxiliary unknowns:

        * ``aux[0]`` — sense branch current ``I_ctrl``
          (zero-volt source between ctrl+ and ctrl−).
        * ``aux[1]`` — output branch current ``I_H``.
        """
        self._aux_indices.append(nodeManager.RequestAuxiliaryUnknown())
        self._aux_indices.append(nodeManager.RequestAuxiliaryUnknown())

    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        """
        Stamp the CCVS into the MNA system.

        **Sense element** (zero-volt source, aux[0] = ``I_ctrl``)::

            V(ctrl+) − V(ctrl−) = 0

        **Output element** (aux[1] = ``I_H``)::

            V(out+) − V(out−) − r · I_ctrl = 0
        """
        op = self.Nodes[0].Index
        om = self.Nodes[1].Index
        cp = self._ctrl_nodes[0].Index
        cm = self._ctrl_nodes[1].Index
        i_sense = self.AuxIndices[0]   # I_ctrl
        i_out   = self.AuxIndices[1]   # I_H
        r = self._rm

        # ── sense element: zero-volt source between ctrl+ and ctrl− ─
        if cp is not None:
            A[i_sense, cp] += 1
            A[cp, i_sense] += 1
        if cm is not None:
            A[i_sense, cm] -= 1
            A[cm, i_sense] -= 1
        # b[i_sense] = 0  (zero volts)

        # ── output element: V(out+) − V(out−) = r · I_ctrl ──────────
        if op is not None:
            A[i_out, op] += 1
            A[op, i_out] += 1
        if om is not None:
            A[i_out, om] -= 1
            A[om, i_out] -= 1
        # Controlling term: −r · I_ctrl
        A[i_out, i_sense] -= r

    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        pass

    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """Return the output branch current ``I_H``."""
        return float(solutionVector[self.AuxIndices[1]])

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return ``V(out+) − V(out−)``."""
        op, om = self.Nodes
        v1 = float(solutionVector[op.Index]) if op.Index is not None else 0.0
        v2 = float(solutionVector[om.Index]) if om.Index is not None else 0.0
        return v1 - v2

    def GetSenseCurrent(self, solutionVector: np.ndarray) -> float:
        """Return the controlling (sense) branch current ``I_ctrl``."""
        return float(solutionVector[self.AuxIndices[0]])


# ════════════════════════════════════════════════════════════════════
#  CCCS — Current-Controlled Current Source  (F)
# ════════════════════════════════════════════════════════════════════

class CCCS(Component):
    """
    Current-Controlled Current Source (F-source).

    ``I_out = α · I_ctrl``

    The controlling current ``I_ctrl`` is sensed by inserting a
    zero-volt voltage source between ``ctrl+`` and ``ctrl−``
    (current flows from ``ctrl+`` to ``ctrl−``).

    Parameters
    ----------
    name : str
        Component identifier (e.g. ``'F1'``).
    out_nodes : tuple[Node, Node]
        ``(out+, out−)`` — output terminal pair.  Output current
        enters ``out+`` and leaves ``out−``.
    ctrl_nodes : tuple[Node, Node]
        ``(ctrl+, ctrl−)`` — controlling current sense terminals.
    gain : float
        Current gain ``α`` (A/A).  Dimensionless.
    """

    _ctrl_nodes: tuple[Node, Node]
    _alpha: float

    def __init__(self, name: str,
                 out_nodes: tuple[Node, Node],
                 ctrl_nodes: tuple[Node, Node],
                 gain: float):
        super().__init__(name, out_nodes)
        self._ctrl_nodes = ctrl_nodes
        self._alpha = gain

    @property
    def CurrentGain(self) -> float:
        return self._alpha

    @property
    def ControlNodes(self) -> tuple[Node, Node]:
        return self._ctrl_nodes

    # ── MNA interface ───────────────────────────────────────────────
    def RegisterUnknowns(self, nodeManager: NodeManager) -> None:
        """
        One auxiliary unknown for the sense branch current ``I_ctrl``
        (zero-volt source between ctrl+ and ctrl−).
        """
        self._aux_indices.append(nodeManager.RequestAuxiliaryUnknown())

    def Stamp(self, A: np.ndarray, b: np.ndarray,
              context: SimulationContext) -> None:
        """
        Stamp the CCCS into the MNA system.

        **Sense element** (zero-volt source, ``I_ctrl = aux[0]``)::

            V(ctrl+) − V(ctrl−) = 0

        **Output current** ``I_out = α · I_ctrl`` is stamped into the
        KCL equations of ``out+`` and ``out−``.
        """
        op = self.Nodes[0].Index
        om = self.Nodes[1].Index
        cp = self._ctrl_nodes[0].Index
        cm = self._ctrl_nodes[1].Index
        i_sense = self.AuxIndices[0]
        alpha = self._alpha

        # ── sense element: zero-volt source between ctrl+ and ctrl− ─
        if cp is not None:
            A[i_sense, cp] += 1
            A[cp, i_sense] += 1
        if cm is not None:
            A[i_sense, cm] -= 1
            A[cm, i_sense] -= 1

        # ── output current: I_out = α · I_ctrl ──────────────────────
        # enters out+, leaves out−
        if op is not None:
            A[op, i_sense] += alpha
        if om is not None:
            A[om, i_sense] -= alpha

    def UpdateState(self, solutionVector: np.ndarray,
                    context: SimulationContext) -> None:
        pass

    def GetCurrent(self, solutionVector: np.ndarray) -> float:
        """Return the output current ``I_out = α · I_ctrl``."""
        i_ctrl = float(solutionVector[self.AuxIndices[0]])
        return self._alpha * i_ctrl

    def GetVoltage(self, solutionVector: np.ndarray) -> float:
        """Return ``V(out+) − V(out−)``."""
        op, om = self.Nodes
        v1 = float(solutionVector[op.Index]) if op.Index is not None else 0.0
        v2 = float(solutionVector[om.Index]) if om.Index is not None else 0.0
        return v1 - v2

    def GetSenseCurrent(self, solutionVector: np.ndarray) -> float:
        """Return the controlling (sense) branch current ``I_ctrl``."""
        return float(solutionVector[self.AuxIndices[0]])
