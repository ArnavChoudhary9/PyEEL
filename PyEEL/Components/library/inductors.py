"""Standard inductor values — axial, radial, and power inductors."""

from __future__ import annotations

from ...Core.Node import Node
from ..Passive.Inductor import Inductor


# ── Small (µH) — RF, SMPS, filtering ───────────────────────────────

def L1u(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """1 µH inductor — RF / SMPS."""
    return Inductor(name, nodes, inductance=1e-6, **kw)


def L4u7(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """4.7 µH inductor — SMPS."""
    return Inductor(name, nodes, inductance=4.7e-6, **kw)


def L10u(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """10 µH inductor — SMPS / filtering."""
    return Inductor(name, nodes, inductance=10e-6, **kw)


def L22u(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """22 µH inductor."""
    return Inductor(name, nodes, inductance=22e-6, **kw)


def L47u(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """47 µH inductor."""
    return Inductor(name, nodes, inductance=47e-6, **kw)


def L100u(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """100 µH inductor."""
    return Inductor(name, nodes, inductance=100e-6, **kw)


def L220u(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """220 µH inductor."""
    return Inductor(name, nodes, inductance=220e-6, **kw)


def L470u(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """470 µH inductor."""
    return Inductor(name, nodes, inductance=470e-6, **kw)


# ── Medium (mH) — audio, general filtering ──────────────────────────

def L1m(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """1 mH inductor — audio / filtering."""
    return Inductor(name, nodes, inductance=1e-3, **kw)


def L2m2(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """2.2 mH inductor."""
    return Inductor(name, nodes, inductance=2.2e-3, **kw)


def L4m7(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """4.7 mH inductor."""
    return Inductor(name, nodes, inductance=4.7e-3, **kw)


def L10m(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """10 mH inductor — audio crossover."""
    return Inductor(name, nodes, inductance=10e-3, **kw)


def L22m(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """22 mH inductor."""
    return Inductor(name, nodes, inductance=22e-3, **kw)


def L47m(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """47 mH inductor."""
    return Inductor(name, nodes, inductance=47e-3, **kw)


def L100m(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """100 mH inductor — mains filter."""
    return Inductor(name, nodes, inductance=100e-3, **kw)


# ── Large (H) — mains / coupled ─────────────────────────────────────

def L1H(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """1 H inductor — mains transformer winding."""
    return Inductor(name, nodes, inductance=1.0, **kw)


def L10H(name: str, nodes: tuple[Node, Node], **kw) -> Inductor:
    """10 H inductor — large mains winding."""
    return Inductor(name, nodes, inductance=10.0, **kw)
