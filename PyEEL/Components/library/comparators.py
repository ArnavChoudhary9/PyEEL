"""Comparator library — popular voltage comparators with datasheet parameters."""

from __future__ import annotations

from ...Core.Node import Node
from ..ICs.Comparator import Comparator


# =====================================================================
#  Open-Collector Comparators  nodes = (non_inv, inv, output)
# =====================================================================

def LM393(name: str, nodes: tuple[Node, Node, Node], **kw) -> Comparator:
    """LM393 — dual open-collector comparator (5 V supply).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return Comparator(name, nodes, V_high=5.0, V_low=0.0,
                      R_in=200e3, R_out=50.0, **kw)


def LM339(name: str, nodes: tuple[Node, Node, Node], **kw) -> Comparator:
    """LM339 — quad open-collector comparator (5 V supply).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return Comparator(name, nodes, V_high=5.0, V_low=0.0,
                      R_in=200e3, R_out=50.0, **kw)


def LM311(name: str, nodes: tuple[Node, Node, Node], **kw) -> Comparator:
    """LM311 — single high-speed comparator (5 V supply).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return Comparator(name, nodes, V_high=5.0, V_low=0.0,
                      R_in=400e3, R_out=30.0, **kw)


def LM2903(name: str, nodes: tuple[Node, Node, Node], **kw) -> Comparator:
    """LM2903 — dual comparator, wide Vcc range (2–36 V).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return Comparator(name, nodes, V_high=5.0, V_low=0.0,
                      R_in=250e3, R_out=50.0, **kw)


# =====================================================================
#  Push-Pull Comparators
# =====================================================================

def TLV3201(name: str, nodes: tuple[Node, Node, Node], **kw) -> Comparator:
    """TLV3201 — single low-power push-pull comparator (3.3 V / 5 V).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return Comparator(name, nodes, V_high=3.3, V_low=0.0,
                      R_in=1e6, R_out=30.0, **kw)


def TLV3501(name: str, nodes: tuple[Node, Node, Node], **kw) -> Comparator:
    """TLV3501 — single high-speed rail-to-rail comparator (4.5 ns).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return Comparator(name, nodes, V_high=3.3, V_low=0.0,
                      R_in=1e6, R_out=20.0, **kw)


def MAX9021(name: str, nodes: tuple[Node, Node, Node], **kw) -> Comparator:
    """MAX9021 — single nano-power push-pull comparator (1.8–5.5 V).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return Comparator(name, nodes, V_high=3.3, V_low=0.0,
                      R_in=1e6, R_out=40.0, **kw)


def MAX9042(name: str, nodes: tuple[Node, Node, Node], **kw) -> Comparator:
    """MAX9042 — dual ultra-low-power comparator (1.8–5.5 V).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return Comparator(name, nodes, V_high=3.3, V_low=0.0,
                      R_in=1e6, R_out=40.0, **kw)


# =====================================================================
#  Ideal Comparator
# =====================================================================

def IdealComparator(name: str, nodes: tuple[Node, Node, Node], **kw) -> Comparator:
    """Ideal comparator — no delay, infinite R_in, near-zero R_out.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return Comparator(name, nodes, V_high=5.0, V_low=0.0,
                      R_in=1e12, R_out=0.001, **kw)
