"""BJT library — NPN, PNP, and Darlington transistors with datasheet parameters."""

from __future__ import annotations

from ...Core.Node import Node
from ..Semiconductors.BJT import BJT, BJTType


# =====================================================================
#  NPN Transistors            nodes = (collector, base, emitter)
# =====================================================================

def N2N2222(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """2N2222 — general-purpose fast-switching NPN (40 V, 800 mA).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=14.34e-15, BF=255.9, BR=6.092,
               Nf=1.0, Nr=1.0, Vaf=74.03, **kw)


def N2N2222A(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """2N2222A — improved 2N2222: higher breakdown (75 V, 800 mA).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=14.34e-15, BF=280.0, BR=6.092,
               Nf=1.0, Nr=1.0, Vaf=74.03, **kw)


def N2N3904(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """2N3904 — general-purpose low-power NPN (40 V, 200 mA).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=6.734e-15, BF=416.4, BR=0.7389,
               Nf=1.0, Nr=1.0, Vaf=74.03, **kw)


def BC547(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """BC547 — general-purpose small-signal NPN (45 V, 100 mA).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.8e-14, BF=400.0, BR=35.5,
               Nf=1.0, Nr=1.0, Vaf=80.0, **kw)


def BC547B(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """BC547B — medium-gain NPN (45 V, 100 mA, hFE 200–450).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.8e-14, BF=325.0, BR=35.5,
               Nf=1.0, Nr=1.0, Vaf=80.0, **kw)


def BC548(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """BC548 — general-purpose small-signal NPN (30 V, 100 mA).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.8e-14, BF=400.0, BR=35.5,
               Nf=1.0, Nr=1.0, Vaf=80.0, **kw)


def BC549(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """BC549 — low-noise small-signal NPN (30 V, 100 mA).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.8e-14, BF=420.0, BR=35.5,
               Nf=1.0, Nr=1.0, Vaf=80.0, **kw)


def BC337(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """BC337 — medium-current NPN (45 V, 800 mA).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.5e-14, BF=350.0, BR=10.0,
               Nf=1.0, Nr=1.0, Vaf=90.0, **kw)


def TIP31C(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """TIP31C — medium-power NPN (100 V, 3 A, 40 W).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.0e-12, BF=50.0, BR=4.0,
               Nf=1.0, Nr=1.0, Vaf=100.0, **kw)


def TIP41C(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """TIP41C — high-power NPN (100 V, 6 A, 65 W).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.0e-12, BF=60.0, BR=4.0,
               Nf=1.0, Nr=1.0, Vaf=100.0, **kw)


def N2N3055(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """2N3055 — classic high-power NPN (60 V, 15 A, 115 W).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=2.0e-11, BF=50.0, BR=4.0,
               Nf=1.0, Nr=1.0, Vaf=100.0, **kw)


def BD139(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """BD139 — medium-power NPN (80 V, 1.5 A, 12.5 W).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.0e-13, BF=100.0, BR=5.0,
               Nf=1.0, Nr=1.0, Vaf=80.0, **kw)


def S8050(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """S8050 — low-voltage, high-current NPN (25 V, 1.5 A).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.0e-14, BF=200.0, BR=5.0,
               Nf=1.0, Nr=1.0, Vaf=50.0, **kw)


def MPSA42(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """MPSA42 — high-voltage NPN (300 V, 500 mA).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=5.0e-15, BF=50.0, BR=4.0,
               Nf=1.0, Nr=1.0, Vaf=100.0, **kw)


# =====================================================================
#  PNP Transistors            nodes = (collector, base, emitter)
# =====================================================================

def N2N3906(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """2N3906 — general-purpose low-power PNP (40 V, 200 mA).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=1.305e-14, BF=180.7, BR=4.977,
               Nf=1.0, Nr=1.0, Vaf=18.7, **kw)


def N2N2907(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """2N2907 — general-purpose PNP (60 V, 600 mA).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=6.5e-15, BF=200.0, BR=4.0,
               Nf=1.0, Nr=1.0, Vaf=115.0, **kw)


def BC557(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """BC557 — general-purpose small-signal PNP (45 V, 100 mA).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=1.8e-14, BF=330.0, BR=35.0,
               Nf=1.0, Nr=1.0, Vaf=60.0, **kw)


def BC558(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """BC558 — general-purpose small-signal PNP (30 V, 100 mA).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=1.8e-14, BF=330.0, BR=35.0,
               Nf=1.0, Nr=1.0, Vaf=60.0, **kw)


def TIP32C(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """TIP32C — medium-power PNP (100 V, 3 A, 40 W).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=1.0e-12, BF=50.0, BR=4.0,
               Nf=1.0, Nr=1.0, Vaf=100.0, **kw)


def TIP42C(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """TIP42C — high-power PNP (100 V, 6 A, 65 W).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=1.0e-12, BF=60.0, BR=4.0,
               Nf=1.0, Nr=1.0, Vaf=100.0, **kw)


def BD140(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """BD140 — medium-power PNP (80 V, 1.5 A, 12.5 W).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=1.0e-13, BF=100.0, BR=5.0,
               Nf=1.0, Nr=1.0, Vaf=80.0, **kw)


def S8550(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """S8550 — low-voltage, high-current PNP (25 V, 1.5 A).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=1.0e-14, BF=200.0, BR=5.0,
               Nf=1.0, Nr=1.0, Vaf=50.0, **kw)


def MPSA92(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """MPSA92 — high-voltage PNP (300 V, 500 mA).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=5.0e-15, BF=50.0, BR=4.0,
               Nf=1.0, Nr=1.0, Vaf=100.0, **kw)


# =====================================================================
#  Darlington Transistors     nodes = (collector, base, emitter)
# =====================================================================

def TIP120(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """TIP120 — NPN Darlington (60 V, 5 A, 65 W), hFE ≥ 1000.

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=6.8e-10, BF=1000.0, BR=10.0,
               Nf=1.5, Nr=1.0, Vaf=100.0, **kw)


def TIP121(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """TIP121 — NPN Darlington (80 V, 5 A, 65 W), hFE ≥ 1000.

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=6.8e-10, BF=1000.0, BR=10.0,
               Nf=1.5, Nr=1.0, Vaf=100.0, **kw)


def TIP122(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """TIP122 — NPN Darlington (100 V, 5 A, 65 W), hFE ≥ 1000.

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=6.8e-10, BF=1000.0, BR=10.0,
               Nf=1.5, Nr=1.0, Vaf=100.0, **kw)


def TIP125(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """TIP125 — PNP Darlington (60 V, 5 A, 65 W), hFE ≥ 1000.

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=6.8e-10, BF=1000.0, BR=10.0,
               Nf=1.5, Nr=1.0, Vaf=100.0, **kw)


def TIP126(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """TIP126 — PNP Darlington (80 V, 5 A, 65 W), hFE ≥ 1000.

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=6.8e-10, BF=1000.0, BR=10.0,
               Nf=1.5, Nr=1.0, Vaf=100.0, **kw)


def TIP127(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """TIP127 — PNP Darlington (100 V, 5 A, 65 W), hFE ≥ 1000.

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=6.8e-10, BF=1000.0, BR=10.0,
               Nf=1.5, Nr=1.0, Vaf=100.0, **kw)


def N2N5306(name: str, nodes: tuple[Node, Node, Node], **kw) -> BJT:
    """2N5306 — high-gain small-signal NPN Darlington.

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.0e-10, BF=2500.0, BR=10.0,
               Nf=1.5, Nr=1.0, Vaf=100.0, **kw)
