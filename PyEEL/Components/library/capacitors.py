"""Standard capacitor values — ceramic, film, and electrolytic."""

from __future__ import annotations

from ...Core.Node import Node
from ..Passive.Capacitor import Capacitor


# ── Ceramic / Film (small values) ───────────────────────────────────

def C10p(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """10 pF ceramic capacitor."""
    return Capacitor(name, nodes, capacitance=10e-12, **kw)


def C22p(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """22 pF ceramic capacitor (crystal load cap)."""
    return Capacitor(name, nodes, capacitance=22e-12, **kw)


def C47p(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """47 pF ceramic capacitor."""
    return Capacitor(name, nodes, capacitance=47e-12, **kw)


def C100p(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """100 pF ceramic capacitor."""
    return Capacitor(name, nodes, capacitance=100e-12, **kw)


def C220p(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """220 pF ceramic capacitor."""
    return Capacitor(name, nodes, capacitance=220e-12, **kw)


def C1n(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """1 nF ceramic / film capacitor."""
    return Capacitor(name, nodes, capacitance=1e-9, **kw)


def C10n(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """10 nF ceramic / film capacitor."""
    return Capacitor(name, nodes, capacitance=10e-9, **kw)


def C22n(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """22 nF ceramic / film capacitor."""
    return Capacitor(name, nodes, capacitance=22e-9, **kw)


def C47n(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """47 nF ceramic / film capacitor."""
    return Capacitor(name, nodes, capacitance=47e-9, **kw)


def C100n(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """100 nF (0.1 µF) ceramic capacitor — universal decoupling cap."""
    return Capacitor(name, nodes, capacitance=100e-9, **kw)


# ── Electrolytic / Film (larger values) ─────────────────────────────

def C1u(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """1 µF capacitor."""
    return Capacitor(name, nodes, capacitance=1e-6, **kw)


def C2u2(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """2.2 µF capacitor."""
    return Capacitor(name, nodes, capacitance=2.2e-6, **kw)


def C4u7(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """4.7 µF capacitor."""
    return Capacitor(name, nodes, capacitance=4.7e-6, **kw)


def C10u(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """10 µF electrolytic capacitor."""
    return Capacitor(name, nodes, capacitance=10e-6, **kw)


def C22u(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """22 µF electrolytic capacitor."""
    return Capacitor(name, nodes, capacitance=22e-6, **kw)


def C47u(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """47 µF electrolytic capacitor."""
    return Capacitor(name, nodes, capacitance=47e-6, **kw)


def C100u(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """100 µF electrolytic capacitor."""
    return Capacitor(name, nodes, capacitance=100e-6, **kw)


def C220u(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """220 µF electrolytic capacitor."""
    return Capacitor(name, nodes, capacitance=220e-6, **kw)


def C470u(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """470 µF electrolytic capacitor."""
    return Capacitor(name, nodes, capacitance=470e-6, **kw)


def C1000u(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """1000 µF electrolytic capacitor — common PSU filter cap."""
    return Capacitor(name, nodes, capacitance=1000e-6, **kw)


def C2200u(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """2200 µF electrolytic capacitor — heavy PSU filter cap."""
    return Capacitor(name, nodes, capacitance=2200e-6, **kw)


def C4700u(name: str, nodes: tuple[Node, Node], **kw) -> Capacitor:
    """4700 µF electrolytic capacitor — bulk filter cap."""
    return Capacitor(name, nodes, capacitance=4700e-6, **kw)
