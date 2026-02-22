"""
Core types for the PyEEL circuit simulation framework.

This sub-package contains the foundational data structures —
nodes, node management, simulation configuration — that every
other module depends on.
"""

from .Node import Node
from .NodeManager import NodeManager, GROUND_NODE_NAME
from .SimulationContext import (
    SimulationMode,
    IntegrationMethod,
    SimulationConfig,
    SimulationContext,
)

__all__ = [
    "Node",
    "NodeManager",
    "GROUND_NODE_NAME",
    "SimulationMode",
    "IntegrationMethod",
    "SimulationConfig",
    "SimulationContext",
]
