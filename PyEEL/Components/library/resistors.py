"""Standard resistor values — E24 series + common through-hole values."""

from __future__ import annotations

from ...Core.Node import Node
from ..Passive.Resistor import Resistor


def R10(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """10 Ω resistor."""
    return Resistor(name, nodes, resistance=10.0, **kw)


def R22(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """22 Ω resistor."""
    return Resistor(name, nodes, resistance=22.0, **kw)


def R47(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """47 Ω resistor."""
    return Resistor(name, nodes, resistance=47.0, **kw)


def R100(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """100 Ω resistor."""
    return Resistor(name, nodes, resistance=100.0, **kw)


def R150(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """150 Ω resistor."""
    return Resistor(name, nodes, resistance=150.0, **kw)


def R220(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """220 Ω resistor."""
    return Resistor(name, nodes, resistance=220.0, **kw)


def R330(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """330 Ω resistor."""
    return Resistor(name, nodes, resistance=330.0, **kw)


def R470(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """470 Ω resistor."""
    return Resistor(name, nodes, resistance=470.0, **kw)


def R680(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """680 Ω resistor."""
    return Resistor(name, nodes, resistance=680.0, **kw)


def R1k(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """1 kΩ resistor."""
    return Resistor(name, nodes, resistance=1e3, **kw)


def R1k5(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """1.5 kΩ resistor."""
    return Resistor(name, nodes, resistance=1.5e3, **kw)


def R2k2(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """2.2 kΩ resistor."""
    return Resistor(name, nodes, resistance=2.2e3, **kw)


def R3k3(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """3.3 kΩ resistor."""
    return Resistor(name, nodes, resistance=3.3e3, **kw)


def R4k7(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """4.7 kΩ resistor."""
    return Resistor(name, nodes, resistance=4.7e3, **kw)


def R5k(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """5 kΩ resistor (potentiometer mid-point)."""
    return Resistor(name, nodes, resistance=5e3, **kw)


def R6k8(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """6.8 kΩ resistor."""
    return Resistor(name, nodes, resistance=6.8e3, **kw)


def R10k(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """10 kΩ resistor."""
    return Resistor(name, nodes, resistance=10e3, **kw)


def R15k(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """15 kΩ resistor."""
    return Resistor(name, nodes, resistance=15e3, **kw)


def R22k(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """22 kΩ resistor."""
    return Resistor(name, nodes, resistance=22e3, **kw)


def R33k(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """33 kΩ resistor."""
    return Resistor(name, nodes, resistance=33e3, **kw)


def R47k(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """47 kΩ resistor."""
    return Resistor(name, nodes, resistance=47e3, **kw)


def R56k(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """56 kΩ resistor."""
    return Resistor(name, nodes, resistance=56e3, **kw)


def R68k(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """68 kΩ resistor."""
    return Resistor(name, nodes, resistance=68e3, **kw)


def R100k(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """100 kΩ resistor."""
    return Resistor(name, nodes, resistance=100e3, **kw)


def R220k(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """220 kΩ resistor."""
    return Resistor(name, nodes, resistance=220e3, **kw)


def R470k(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """470 kΩ resistor."""
    return Resistor(name, nodes, resistance=470e3, **kw)


def R1M(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """1 MΩ resistor."""
    return Resistor(name, nodes, resistance=1e6, **kw)


def R10M(name: str, nodes: tuple[Node, Node], **kw) -> Resistor:
    """10 MΩ resistor."""
    return Resistor(name, nodes, resistance=10e6, **kw)
