from .Node import Node

GROUND_NODE_NAME = "GND"


class NodeManager:
    """
    Central registry that owns every :class:`Node` in a circuit.

    Responsibilities
    ----------------
    * Create nodes and assign them sequential MNA indices starting at 0.
    * Maintain the distinguished **ground** node (index ``None``).
    * After :meth:`Freeze` is called, prevent new node creation and allow
      components to request **auxiliary unknowns** (e.g. branch currents
      for voltage sources) whose indices follow the voltage-node block.

    Index layout in the solution vector
    ------------------------------------
    ::

        [  v_0, v_1, …, v_{N-1},      i_aux_0, i_aux_1, …     ]
         \\____ voltage nodes ___/ \\__ auxiliary unknowns __/
    """

    _Nodes: dict[str, Node]
    _GroundNode: Node

    _NextVoltageIndex: int
    _NextAuxiliaryIndex: int

    _NodesFrozen: bool

    def __init__(self):
        self._GroundNode = Node(GROUND_NODE_NAME)
        self._Nodes = {GROUND_NODE_NAME: self._GroundNode}

        self._NextVoltageIndex = 0
        self._NextAuxiliaryIndex = 0

        self._NodesFrozen = False

    # ── properties ──────────────────────────────────────────────────
    @property
    def GroundNode(self) -> Node:
        """The circuit reference (ground) node."""
        return self._GroundNode

    @property
    def VoltageUnknownCount(self) -> int:
        """Number of voltage unknowns (non-ground nodes)."""
        return self._NextVoltageIndex

    @property
    def AuxiliaryUnknownCount(self) -> int:
        """Number of auxiliary unknowns (branch currents, etc.)."""
        return self._NextAuxiliaryIndex

    @property
    def TotalUnknownCount(self) -> int:
        """Total size of the MNA system (voltages + auxiliary)."""
        return self._NextVoltageIndex + self._NextAuxiliaryIndex

    @property
    def NodesFrozen(self) -> bool:
        """``True`` after :meth:`Freeze` has been called."""
        return self._NodesFrozen

    # ── mutation ────────────────────────────────────────────────────
    def Freeze(self) -> None:
        """Lock the topology — no more nodes may be added after this."""
        if self._NodesFrozen:
            raise RuntimeError("NodeManager is already frozen.")

        if self._NextVoltageIndex == 0:
            raise RuntimeError(
                "Circuit must have at least one non-ground node "
                "before freezing the NodeManager."
            )

        self._NodesFrozen = True

    def AddNode(self, name: str) -> Node:
        """
        Create a new voltage node and assign it the next available index.

        Raises
        ------
        RuntimeError
            If the manager is already frozen.
        ValueError
            If a node with *name* already exists.
        """
        if self._NodesFrozen:
            raise RuntimeError("Cannot add node to a frozen NodeManager.")

        if name in self._Nodes:
            raise ValueError(f"Node with name '{name}' already exists.")

        node = Node(name)
        node.SetIndex(self._NextVoltageIndex)
        self._Nodes[node.Name] = node

        self._NextVoltageIndex += 1
        return node

    def GetNode(self, name: str, create_if_missing: bool = False) -> Node | None:
        """
        Look up a node by name.

        Parameters
        ----------
        name : str
            The node's unique name.
        create_if_missing : bool
            When ``True`` *and* the manager is not frozen, a new node is
            created automatically if one with *name* does not exist.

        Returns
        -------
        Node or None
            The node, or ``None`` when the name is unknown and
            *create_if_missing* is ``False``.
        """
        if name not in self._Nodes and create_if_missing and not self._NodesFrozen:
            return self.AddNode(name)

        return self._Nodes.get(name, None)

    def RequestAuxiliaryUnknown(self) -> int:
        """
        Allocate the next auxiliary unknown index (used by voltage sources
        and other components that introduce extra KCL/KVL equations).

        Must be called *after* :meth:`Freeze`.
        """
        if not self._NodesFrozen:
            raise RuntimeError(
                "Cannot request auxiliary unknown before nodes are frozen."
            )

        index = self._NextVoltageIndex + self._NextAuxiliaryIndex
        self._NextAuxiliaryIndex += 1
        return index
