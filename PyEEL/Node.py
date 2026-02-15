class Node:
    """
    Represents a single electrical node (net) in a circuit.

    Each node has a unique name and an optional integer index that maps it
    into the MNA solution vector.  The ground node has ``Index = None``;
    every other node is assigned a non-negative index by the
    :class:`NodeManager` when it is created.
    """

    _Name: str
    _Index: int | None

    def __init__(self, name: str, index: int | None = None):
        self._Name = name
        self._Index = index

    # ── properties ──────────────────────────────────────────────────
    @property
    def Name(self) -> str:
        """Human-readable node name."""
        return self._Name

    @property
    def Index(self) -> int | None:
        """Row / column index in the MNA matrix, or ``None`` for ground."""
        return self._Index

    @property
    def IsGround(self) -> bool:
        """``True`` when this node is the reference (ground) node."""
        return self._Index is None

    # ── mutators ────────────────────────────────────────────────────
    def SetIndex(self, index: int | None) -> None:
        """Assign or clear the MNA index.  Called by :class:`NodeManager`."""
        self._Index = index

    # ── identity & display ──────────────────────────────────────────
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return NotImplemented
        return self._Name == other._Name

    def __hash__(self) -> int:
        return hash(self._Name)

    def __repr__(self) -> str:
        idx = self._Index if self._Index is not None else "Ground"
        return f"Node({self._Name!r}, {idx})"

    def __str__(self) -> str:
        if self._Index is not None:
            return f"{self._Name}[{self._Index}]"
        return f"{self._Name}[Ground]"
