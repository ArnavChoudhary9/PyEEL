"""Backward-compatibility shim. Import from ``PyEEL.Core.NodeManager`` instead."""
from .Core.NodeManager import NodeManager, GROUND_NODE_NAME
__all__ = ["NodeManager", "GROUND_NODE_NAME"]
