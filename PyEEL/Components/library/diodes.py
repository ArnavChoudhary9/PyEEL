"""Diode library — rectifiers, signal, Schottky, and LEDs with datasheet parameters."""

from __future__ import annotations

from ...Core.Node import Node
from ..Semiconductors.Diode import Diode


# =====================================================================
#  Rectifier Diodes           nodes = (anode, cathode)
# =====================================================================

def IN4001(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """1N4001 — general-purpose rectifier (50 V, 1 A).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=2.55e-9, n=1.75, **kw)


def IN4002(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """1N4002 — general-purpose rectifier (100 V, 1 A).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=2.55e-9, n=1.75, **kw)


def IN4004(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """1N4004 — general-purpose rectifier (400 V, 1 A).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=4.0e-9, n=1.76, **kw)


def IN4007(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """1N4007 — general-purpose rectifier (1000 V, 1 A).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=7.02e-9, n=1.77, **kw)


def IN5399(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """1N5399 — power rectifier (1000 V, 1.5 A).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=8.0e-9, n=1.77, **kw)


def IN5408(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """1N5408 — power rectifier (1000 V, 3 A).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=4.5e-9, n=1.8, **kw)


# =====================================================================
#  Signal Diodes              nodes = (anode, cathode)
# =====================================================================

def IN4148(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """1N4148 — fast signal diode (75 V, 200 mA, t_rr ≈ 4 ns).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=2.52e-9, n=1.75, **kw)


def IN914(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """1N914 — fast switching signal diode (same as 1N4148).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=2.52e-9, n=1.75, **kw)


def IN4454(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """1N4454 — high-speed signal diode (75 V, 200 mA).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=2.0e-9, n=1.75, **kw)


# =====================================================================
#  Schottky Diodes            nodes = (anode, cathode)
# =====================================================================

def IN5817(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """1N5817 — Schottky barrier diode (20 V, 1 A, V_f ≈ 0.32 V).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=3.19e-5, n=1.05, **kw)


def IN5819(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """1N5819 — Schottky barrier diode (40 V, 1 A, V_f ≈ 0.34 V).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=2.5e-5, n=1.05, **kw)


def IN5822(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """1N5822 — Schottky power diode (40 V, 3 A, V_f ≈ 0.52 V).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=5.0e-5, n=1.06, **kw)


def BAT54(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """BAT54 — small-signal Schottky (30 V, 200 mA, V_f ≈ 0.24 V).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=1.0e-5, n=1.03, **kw)


def BAT46(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """BAT46 — small-signal Schottky (100 V, 150 mA, V_f ≈ 0.35 V).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=3.0e-6, n=1.04, **kw)


# =====================================================================
#  LEDs                       nodes = (anode, cathode)
# =====================================================================

def LED_Red(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """Standard red LED (V_f ≈ 1.8 V, 20 mA).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=1.2e-20, n=1.8, **kw)


def LED_Orange(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """Standard orange LED (V_f ≈ 2.0 V, 20 mA).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=5.0e-21, n=1.85, **kw)


def LED_Yellow(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """Standard yellow LED (V_f ≈ 2.0 V, 20 mA).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=5.0e-22, n=1.85, **kw)


def LED_Green(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """Standard green LED (V_f ≈ 2.1 V, 20 mA).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=1.0e-22, n=1.9, **kw)


def LED_Blue(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """Standard blue LED (V_f ≈ 3.2 V, 20 mA).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=1.0e-30, n=2.1, **kw)


def LED_White(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """Standard white LED (V_f ≈ 3.2 V, 20 mA).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=1.0e-30, n=2.1, **kw)


def LED_IR(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """Infrared LED (V_f ≈ 1.2 V, 20 mA, 940 nm).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=1.0e-15, n=1.6, **kw)


def LED_UV(name: str, nodes: tuple[Node, Node], **kw) -> Diode:
    """Ultraviolet LED (V_f ≈ 3.5 V, 20 mA, 395 nm).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=1.0e-33, n=2.2, **kw)
