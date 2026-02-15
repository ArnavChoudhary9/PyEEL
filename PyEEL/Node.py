class Node:
    _Name: str
    _Index: int | None
    
    def __init__(self, name: str, index: int | None = None):
        self._Name = name
        self._Index = index
        
    @property
    def Name(self) -> str: return self._Name
    @property
    def Index(self) -> int | None: return self._Index
    @property
    def IsGround(self) -> bool: return self._Index is None

    def SetIndex(self, index: int | None) -> None: self._Index = index
    
    def __str__(self) -> str:
        if self._Index is not None:
            return f"{self._Name}[{self._Index}]"
        return f"{self._Name}[Ground]"
