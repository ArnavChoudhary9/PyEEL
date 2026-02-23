"""MOSFET library — N-channel and P-channel devices with datasheet parameters."""

from __future__ import annotations

from ...Core.Node import Node
from ..Semiconductors.MOSFET import MOSFET, MOSFETType


# =====================================================================
#  N-Channel MOSFETs          nodes = (drain, gate, source)
# =====================================================================

def N2N7000(name: str, nodes: tuple[Node, Node, Node], **kw) -> MOSFET:
    """2N7000 — small-signal NMOS (60 V, 200 mA, TO-92).

    ``nodes = (drain, gate, source)``
    """
    return MOSFET(name, nodes, MOSFETType.NMOS,
                  Kp=0.1, Vth=2.1, lambda_=0.01, **kw)


def BS170(name: str, nodes: tuple[Node, Node, Node], **kw) -> MOSFET:
    """BS170 — small-signal NMOS (60 V, 500 mA, TO-92).

    ``nodes = (drain, gate, source)``
    """
    return MOSFET(name, nodes, MOSFETType.NMOS,
                  Kp=0.2, Vth=2.0, lambda_=0.01, **kw)


def IRLZ44N(name: str, nodes: tuple[Node, Node, Node], **kw) -> MOSFET:
    """IRLZ44N — logic-level power NMOS (55 V, 47 A, TO-220).

    ``nodes = (drain, gate, source)``
    """
    return MOSFET(name, nodes, MOSFETType.NMOS,
                  Kp=60.0, Vth=1.5, lambda_=0.005, **kw)


def IRF520N(name: str, nodes: tuple[Node, Node, Node], **kw) -> MOSFET:
    """IRF520N — power NMOS (100 V, 9.7 A, TO-220).

    ``nodes = (drain, gate, source)``
    """
    return MOSFET(name, nodes, MOSFETType.NMOS,
                  Kp=10.0, Vth=3.0, lambda_=0.008, **kw)


def IRF530N(name: str, nodes: tuple[Node, Node, Node], **kw) -> MOSFET:
    """IRF530N — power NMOS (100 V, 17 A, TO-220).

    ``nodes = (drain, gate, source)``
    """
    return MOSFET(name, nodes, MOSFETType.NMOS,
                  Kp=15.0, Vth=3.0, lambda_=0.008, **kw)


def IRF540N(name: str, nodes: tuple[Node, Node, Node], **kw) -> MOSFET:
    """IRF540N — power NMOS (100 V, 33 A, TO-220).

    ``nodes = (drain, gate, source)``
    """
    return MOSFET(name, nodes, MOSFETType.NMOS,
                  Kp=20.0, Vth=3.0, lambda_=0.01, **kw)


def IRF640N(name: str, nodes: tuple[Node, Node, Node], **kw) -> MOSFET:
    """IRF640N — power NMOS (200 V, 18 A, TO-220).

    ``nodes = (drain, gate, source)``
    """
    return MOSFET(name, nodes, MOSFETType.NMOS,
                  Kp=12.0, Vth=3.5, lambda_=0.006, **kw)


def IRF840(name: str, nodes: tuple[Node, Node, Node], **kw) -> MOSFET:
    """IRF840 — high-voltage NMOS (500 V, 8 A, TO-220).

    ``nodes = (drain, gate, source)``
    """
    return MOSFET(name, nodes, MOSFETType.NMOS,
                  Kp=5.0, Vth=3.5, lambda_=0.003, **kw)


def IRFZ44N(name: str, nodes: tuple[Node, Node, Node], **kw) -> MOSFET:
    """IRFZ44N — power NMOS (55 V, 49 A, TO-220).

    ``nodes = (drain, gate, source)``
    """
    return MOSFET(name, nodes, MOSFETType.NMOS,
                  Kp=50.0, Vth=3.0, lambda_=0.01, **kw)


def AO3400(name: str, nodes: tuple[Node, Node, Node], **kw) -> MOSFET:
    """AO3400 — N-channel MOSFET SOT-23 (30 V, 5.7 A).

    ``nodes = (drain, gate, source)``
    """
    return MOSFET(name, nodes, MOSFETType.NMOS,
                  Kp=5.0, Vth=1.2, lambda_=0.02, **kw)


# =====================================================================
#  P-Channel MOSFETs          nodes = (drain, gate, source)
# =====================================================================

def IRF9540N(name: str, nodes: tuple[Node, Node, Node], **kw) -> MOSFET:
    """IRF9540N — power PMOS (100 V, 23 A, TO-220).

    ``nodes = (drain, gate, source)``
    """
    return MOSFET(name, nodes, MOSFETType.PMOS,
                  Kp=10.0, Vth=-3.5, lambda_=0.01, **kw)


def IRF9530N(name: str, nodes: tuple[Node, Node, Node], **kw) -> MOSFET:
    """IRF9530N — power PMOS (100 V, 14 A, TO-220).

    ``nodes = (drain, gate, source)``
    """
    return MOSFET(name, nodes, MOSFETType.PMOS,
                  Kp=7.0, Vth=-3.5, lambda_=0.01, **kw)


def IRF4905(name: str, nodes: tuple[Node, Node, Node], **kw) -> MOSFET:
    """IRF4905 — power PMOS (55 V, 74 A, TO-220).

    ``nodes = (drain, gate, source)``
    """
    return MOSFET(name, nodes, MOSFETType.PMOS,
                  Kp=40.0, Vth=-2.5, lambda_=0.008, **kw)


def BS250(name: str, nodes: tuple[Node, Node, Node], **kw) -> MOSFET:
    """BS250 — small-signal PMOS (45 V, 180 mA, TO-92).

    ``nodes = (drain, gate, source)``
    """
    return MOSFET(name, nodes, MOSFETType.PMOS,
                  Kp=0.1, Vth=-2.5, lambda_=0.01, **kw)


def AO3401(name: str, nodes: tuple[Node, Node, Node], **kw) -> MOSFET:
    """AO3401 — P-channel MOSFET SOT-23 (30 V, 4 A).

    ``nodes = (drain, gate, source)``
    """
    return MOSFET(name, nodes, MOSFETType.PMOS,
                  Kp=3.5, Vth=-1.2, lambda_=0.02, **kw)
