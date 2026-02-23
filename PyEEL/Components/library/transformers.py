"""Transformer presets — common mains step-down transformers."""

from __future__ import annotations

from ...Core.Node import Node
from ..Magnetic.Transformer import Transformer


# =====================================================================
#  240 V mains (50 Hz) transformers
# =====================================================================

def Transformer_240_to_5(
    name: str,
    primary_nodes: tuple[Node, Node],
    secondary_nodes: tuple[Node, Node],
    **kw,
) -> Transformer:
    """240 V → 5 V step-down transformer (turns ratio ≈ 48:1).

    ``primary_nodes = (p+, p-)``, ``secondary_nodes = (s+, s-)``
    """
    return Transformer(name, primary_nodes, secondary_nodes,
                       primary_inductance=100.0,
                       secondary_inductance=0.0434, k=0.999, **kw)


def Transformer_240_to_9(
    name: str,
    primary_nodes: tuple[Node, Node],
    secondary_nodes: tuple[Node, Node],
    **kw,
) -> Transformer:
    """240 V → 9 V step-down transformer (turns ratio ≈ 26.7:1).

    ``primary_nodes = (p+, p-)``, ``secondary_nodes = (s+, s-)``
    """
    return Transformer(name, primary_nodes, secondary_nodes,
                       primary_inductance=100.0,
                       secondary_inductance=0.1406, k=0.999, **kw)


def Transformer_240_to_12(
    name: str,
    primary_nodes: tuple[Node, Node],
    secondary_nodes: tuple[Node, Node],
    **kw,
) -> Transformer:
    """240 V → 12 V step-down transformer (turns ratio = 20:1).

    ``primary_nodes = (p+, p-)``, ``secondary_nodes = (s+, s-)``
    """
    return Transformer(name, primary_nodes, secondary_nodes,
                       primary_inductance=100.0,
                       secondary_inductance=0.25, k=0.999, **kw)


def Transformer_240_to_24(
    name: str,
    primary_nodes: tuple[Node, Node],
    secondary_nodes: tuple[Node, Node],
    **kw,
) -> Transformer:
    """240 V → 24 V step-down transformer (turns ratio = 10:1).

    ``primary_nodes = (p+, p-)``, ``secondary_nodes = (s+, s-)``
    """
    return Transformer(name, primary_nodes, secondary_nodes,
                       primary_inductance=100.0,
                       secondary_inductance=1.0, k=0.999, **kw)


def Transformer_240_to_48(
    name: str,
    primary_nodes: tuple[Node, Node],
    secondary_nodes: tuple[Node, Node],
    **kw,
) -> Transformer:
    """240 V → 48 V step-down transformer (turns ratio = 5:1).

    ``primary_nodes = (p+, p-)``, ``secondary_nodes = (s+, s-)``
    """
    return Transformer(name, primary_nodes, secondary_nodes,
                       primary_inductance=100.0,
                       secondary_inductance=4.0, k=0.999, **kw)


# =====================================================================
#  120 V mains (60 Hz) transformers
# =====================================================================

def Transformer_120_to_5(
    name: str,
    primary_nodes: tuple[Node, Node],
    secondary_nodes: tuple[Node, Node],
    **kw,
) -> Transformer:
    """120 V → 5 V step-down transformer (turns ratio = 24:1).

    ``primary_nodes = (p+, p-)``, ``secondary_nodes = (s+, s-)``
    """
    return Transformer(name, primary_nodes, secondary_nodes,
                       primary_inductance=100.0,
                       secondary_inductance=0.1736, k=0.999, **kw)


def Transformer_120_to_12(
    name: str,
    primary_nodes: tuple[Node, Node],
    secondary_nodes: tuple[Node, Node],
    **kw,
) -> Transformer:
    """120 V → 12 V step-down transformer (turns ratio = 10:1).

    ``primary_nodes = (p+, p-)``, ``secondary_nodes = (s+, s-)``
    """
    return Transformer(name, primary_nodes, secondary_nodes,
                       primary_inductance=100.0,
                       secondary_inductance=1.0, k=0.999, **kw)


def Transformer_120_to_24(
    name: str,
    primary_nodes: tuple[Node, Node],
    secondary_nodes: tuple[Node, Node],
    **kw,
) -> Transformer:
    """120 V → 24 V step-down transformer (turns ratio = 5:1).

    ``primary_nodes = (p+, p-)``, ``secondary_nodes = (s+, s-)``
    """
    return Transformer(name, primary_nodes, secondary_nodes,
                       primary_inductance=100.0,
                       secondary_inductance=4.0, k=0.999, **kw)
