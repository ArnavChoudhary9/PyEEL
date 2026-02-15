from .Node import Node

GROUND_NODE_NAME = "GND"

class NodeManager:
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
        
    @property
    def GroundNode(self) -> Node: return self._GroundNode
    
    @property 
    def VoltageUnknownCount(self) -> int: return self._NextVoltageIndex
    @property
    def AuxiliaryUnknownCount(self) -> int: return self._NextAuxiliaryIndex
    @property
    def TotalUnknownCount(self) -> int: return self._NextVoltageIndex + self._NextAuxiliaryIndex
    
    @property
    def NodesFrozen(self) -> bool: return self._NodesFrozen
    
    def Freeze(self) -> None:
        if self._NodesFrozen:
            raise RuntimeError("NodeManager is already frozen.")
        
        if self._NextVoltageIndex == 0:
            raise RuntimeError("Circuit must have at least one non-ground node before freezing the NodeManager.")
        
        self._NodesFrozen = True
        
    def AddNode(self, name: str) -> Node:
        if self._NodesFrozen:
            raise RuntimeError("Cannot add node to a frozen NodeManager.")
        
        if name in self._Nodes:
            raise ValueError(f"Node with name '{name}' already exists.")
        
        node = Node(name)
        node.SetIndex(self._NextVoltageIndex)
        self._Nodes[node.Name] = node
        
        self._NextVoltageIndex += 1
        
        return node
    
    # This returns None if the node doesn't exist and create_if_missing is False, otherwise it creates a new node with the given name and returns it.
    def GetNode(self, name: str, create_if_missing: bool = False) -> Node | None:
        if name not in self._Nodes and create_if_missing and not self._NodesFrozen:
            return self.AddNode(name)

        return self._Nodes.get(name, None)
    
    def RequestAuxiliaryUnknown(self) -> int:
        if not self._NodesFrozen:
            raise RuntimeError(
                "Cannot request auxiliary unknown before nodes are frozen."
            )

        index = self._NextVoltageIndex + self._NextAuxiliaryIndex
        self._NextAuxiliaryIndex += 1
        return index
