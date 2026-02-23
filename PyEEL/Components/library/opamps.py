"""Op-amp library — popular operational amplifiers with datasheet parameters."""

from __future__ import annotations

from ...Core.Node import Node
from ..ICs.OpAmp import OpAmp


# =====================================================================
#  General-Purpose Op-Amps    nodes = (non_inv, inv, output)
# =====================================================================

def LM741(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """LM741 — classic general-purpose op-amp.

    A_OL ≈ 200 000, R_in ≈ 2 MΩ, R_out ≈ 75 Ω.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=200_000.0, R_in=2e6, R_out=75.0, **kw)


def LM358(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """LM358 — dual general-purpose op-amp (single-supply capable).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=100_000.0, R_in=2e6, R_out=150.0, **kw)


def LM324(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """LM324 — quad general-purpose op-amp (single-supply capable).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=100_000.0, R_in=2e6, R_out=150.0, **kw)


def UA741(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """µA741 — original general-purpose op-amp (military grade LM741).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=200_000.0, R_in=2e6, R_out=75.0, **kw)


# =====================================================================
#  JFET-Input Op-Amps
# =====================================================================

def TL071(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """TL071 — low-noise JFET-input single op-amp.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=200_000.0, R_in=1e12, R_out=100.0, **kw)


def TL072(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """TL072 — low-noise JFET-input dual op-amp.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=200_000.0, R_in=1e12, R_out=100.0, **kw)


def TL074(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """TL074 — low-noise JFET-input quad op-amp.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=200_000.0, R_in=1e12, R_out=100.0, **kw)


def TL082(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """TL082 — general-purpose JFET-input dual op-amp.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=200_000.0, R_in=1e12, R_out=100.0, **kw)


def TL084(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """TL084 — general-purpose JFET-input quad op-amp.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=200_000.0, R_in=1e12, R_out=100.0, **kw)


# =====================================================================
#  Audio & Low-Noise Op-Amps
# =====================================================================

def NE5532(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """NE5532 — low-noise audio dual op-amp.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=100_000.0, R_in=300e3, R_out=0.3, **kw)


def NE5534(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """NE5534 — low-noise audio single op-amp.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=100_000.0, R_in=100e3, R_out=0.3, **kw)


def OPA2134(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """OPA2134 — high-performance audio dual op-amp (FET input).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=1_000_000.0, R_in=10e12, R_out=1.0, **kw)


def OPA2604(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """OPA2604 — FET-input audio dual op-amp (Burr-Brown).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=1_000_000.0, R_in=10e12, R_out=1.0, **kw)


# =====================================================================
#  Precision Op-Amps
# =====================================================================

def OP07(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """OP07 — ultra-low-offset precision op-amp (V_os ≈ 25 µV).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=500_000.0, R_in=33e6, R_out=60.0, **kw)


def OP27(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """OP27 — low-noise precision op-amp (V_os ≈ 30 µV).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=1_000_000.0, R_in=6e6, R_out=70.0, **kw)


def AD620(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """AD620 — low-cost instrumentation amplifier (modelled as op-amp).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=1_000_000.0, R_in=10e9, R_out=1.0, **kw)


def INA128(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """INA128 — precision instrumentation amplifier (modelled as op-amp).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=1_000_000.0, R_in=10e9, R_out=0.5, **kw)


# =====================================================================
#  Ideal Op-Amp
# =====================================================================

def IdealOpAmp(name: str, nodes: tuple[Node, Node, Node], **kw) -> OpAmp:
    """Ideal op-amp — textbook component.

    A_OL = 10^9, R_in = 10^12, R_out ≈ 0.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=1e9, R_in=1e12, R_out=0.001, **kw)
