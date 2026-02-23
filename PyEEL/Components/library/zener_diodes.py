"""Zener diode library — BZX55 series and common regulator diodes."""

from __future__ import annotations

from ...Core.Node import Node
from ..Semiconductors.ZenerDiode import ZenerDiode


# =====================================================================
#  BZX55C series (500 mW)     nodes = (anode, cathode)
# =====================================================================

def BZX55C2V7(name: str, nodes: tuple[Node, Node], **kw) -> ZenerDiode:
    """BZX55C2V7 — 2.7 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=2.7, Is=1e-14, Ibv=5e-3, n_bv=1.0, **kw)


def BZX55C3V3(name: str, nodes: tuple[Node, Node], **kw) -> ZenerDiode:
    """BZX55C3V3 — 3.3 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=3.3, Is=1e-14, Ibv=5e-3, n_bv=1.0, **kw)


def BZX55C3V9(name: str, nodes: tuple[Node, Node], **kw) -> ZenerDiode:
    """BZX55C3V9 — 3.9 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=3.9, Is=1e-14, Ibv=5e-3, n_bv=1.0, **kw)


def BZX55C4V7(name: str, nodes: tuple[Node, Node], **kw) -> ZenerDiode:
    """BZX55C4V7 — 4.7 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=4.7, Is=1e-14, Ibv=5e-3, n_bv=1.0, **kw)


def BZX55C5V1(name: str, nodes: tuple[Node, Node], **kw) -> ZenerDiode:
    """BZX55C5V1 — 5.1 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=5.1, Is=1e-14, Ibv=5e-3, n_bv=1.0, **kw)


def BZX55C5V6(name: str, nodes: tuple[Node, Node], **kw) -> ZenerDiode:
    """BZX55C5V6 — 5.6 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=5.6, Is=1e-14, Ibv=5e-3, n_bv=1.0, **kw)


def BZX55C6V2(name: str, nodes: tuple[Node, Node], **kw) -> ZenerDiode:
    """BZX55C6V2 — 6.2 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=6.2, Is=1e-14, Ibv=5e-3, n_bv=1.0, **kw)


def BZX55C6V8(name: str, nodes: tuple[Node, Node], **kw) -> ZenerDiode:
    """BZX55C6V8 — 6.8 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=6.8, Is=1e-14, Ibv=3e-3, n_bv=1.0, **kw)


def BZX55C7V5(name: str, nodes: tuple[Node, Node], **kw) -> ZenerDiode:
    """BZX55C7V5 — 7.5 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=7.5, Is=1e-14, Ibv=3e-3, n_bv=1.0, **kw)


def BZX55C9V1(name: str, nodes: tuple[Node, Node], **kw) -> ZenerDiode:
    """BZX55C9V1 — 9.1 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=9.1, Is=1e-14, Ibv=2e-3, n_bv=1.0, **kw)


def BZX55C10(name: str, nodes: tuple[Node, Node], **kw) -> ZenerDiode:
    """BZX55C10 — 10 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=10.0, Is=1e-14, Ibv=2e-3, n_bv=1.0, **kw)


def BZX55C12(name: str, nodes: tuple[Node, Node], **kw) -> ZenerDiode:
    """BZX55C12 — 12 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=12.0, Is=1e-14, Ibv=1e-3, n_bv=1.0, **kw)


def BZX55C15(name: str, nodes: tuple[Node, Node], **kw) -> ZenerDiode:
    """BZX55C15 — 15 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=15.0, Is=1e-14, Ibv=1e-3, n_bv=1.0, **kw)


def BZX55C18(name: str, nodes: tuple[Node, Node], **kw) -> ZenerDiode:
    """BZX55C18 — 18 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=18.0, Is=1e-14, Ibv=0.5e-3, n_bv=1.0, **kw)


def BZX55C24(name: str, nodes: tuple[Node, Node], **kw) -> ZenerDiode:
    """BZX55C24 — 24 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=24.0, Is=1e-14, Ibv=0.5e-3, n_bv=1.0, **kw)


def BZX55C33(name: str, nodes: tuple[Node, Node], **kw) -> ZenerDiode:
    """BZX55C33 — 33 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=33.0, Is=1e-14, Ibv=0.3e-3, n_bv=1.0, **kw)


# =====================================================================
#  Convenience aliases
# =====================================================================

Zener2V7 = BZX55C2V7
Zener3V3 = BZX55C3V3
Zener3V9 = BZX55C3V9
Zener4V7 = BZX55C4V7
Zener5V1 = BZX55C5V1
Zener5V6 = BZX55C5V6
Zener6V2 = BZX55C6V2
Zener6V8 = BZX55C6V8
Zener7V5 = BZX55C7V5
Zener9V1 = BZX55C9V1
Zener10V = BZX55C10
Zener12V = BZX55C12
Zener15V = BZX55C15
Zener18V = BZX55C18
Zener24V = BZX55C24
Zener33V = BZX55C33
