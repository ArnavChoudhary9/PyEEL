from .Node import Node

GROUND_NODE_NAME = "GND"

class NodeManager:
    _Nodes: dict[str, Node]
    _GroundNode: Node
    _NextNodeIndex: int
    
    def __init__(self):
        self._GroundNode = Node(GROUND_NODE_NAME)
        self._Nodes = {GROUND_NODE_NAME: self._GroundNode}
        self._NextNodeIndex = 0
        
    @property
    def GroundNode(self) -> Node: return self._GroundNode
    
    @property 
    def VoltageUnknownCount(self) -> int: return self._NextNodeIndex

        
    def AddNode(self, name: str) -> Node:
        if name in self._Nodes:
            raise ValueError(f"Node with name '{name}' already exists.")
        
        node = Node(name)
        node.SetIndex(self._NextNodeIndex)
        self._Nodes[node.Name] = node
        
        self._NextNodeIndex += 1
        
        return node
    
    # This returns None if the node doesn't exist and create_if_missing is False, otherwise it creates a new node with the given name and returns it.
    def GetNode(self, name: str, create_if_missing: bool = False) -> Node | None:
        if name not in self._Nodes and create_if_missing:
            return self.AddNode(name)

        return self._Nodes.get(name, None)
