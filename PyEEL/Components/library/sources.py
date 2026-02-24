"""Power-source presets — DC and AC supplies with common voltage/frequency values."""

from __future__ import annotations

import math

from ...Core.Node import Node
from ..Sources.VoltageSource import (
    VoltageSource, DCVoltageSource, ACVoltageSource,
)


# ── DC Sources ──────────────────────────────────────────────────────

def DC3V3(name: str, nodes: tuple[Node, Node], **kw) -> VoltageSource:
    """3.3 V DC supply.  ``nodes = (positive, negative)``."""
    return DCVoltageSource(name, nodes, voltage=3.3, **kw)


def DC5V(name: str, nodes: tuple[Node, Node], **kw) -> VoltageSource:
    """5 V DC supply.  ``nodes = (positive, negative)``."""
    return DCVoltageSource(name, nodes, voltage=5.0, **kw)


def DC9V(name: str, nodes: tuple[Node, Node], **kw) -> VoltageSource:
    """9 V DC supply (battery).  ``nodes = (positive, negative)``."""
    return DCVoltageSource(name, nodes, voltage=9.0, **kw)


def DC12V(name: str, nodes: tuple[Node, Node], **kw) -> VoltageSource:
    """12 V DC supply.  ``nodes = (positive, negative)``."""
    return DCVoltageSource(name, nodes, voltage=12.0, **kw)


def DC15V(name: str, nodes: tuple[Node, Node], **kw) -> VoltageSource:
    """15 V DC supply.  ``nodes = (positive, negative)``."""
    return DCVoltageSource(name, nodes, voltage=15.0, **kw)


def DC24V(name: str, nodes: tuple[Node, Node], **kw) -> VoltageSource:
    """24 V DC supply.  ``nodes = (positive, negative)``."""
    return DCVoltageSource(name, nodes, voltage=24.0, **kw)


def DC48V(name: str, nodes: tuple[Node, Node], **kw) -> VoltageSource:
    """48 V DC supply (telecom).  ``nodes = (positive, negative)``."""
    return DCVoltageSource(name, nodes, voltage=48.0, **kw)


# ── AC Sources ──────────────────────────────────────────────────────

def AC240V_50Hz(name: str, nodes: tuple[Node, Node], **kw) -> VoltageSource:
    """240 V RMS, 50 Hz mains supply (peak ≈ 339.4 V).

    ``nodes = (positive, negative)``
    """
    return ACVoltageSource(name, nodes,
                           amplitude=240.0 * math.sqrt(2),
                           frequency=50.0, **kw)


def AC230V_50Hz(name: str, nodes: tuple[Node, Node], **kw) -> VoltageSource:
    """230 V RMS, 50 Hz EU mains supply (peak ≈ 325.3 V).

    ``nodes = (positive, negative)``
    """
    return ACVoltageSource(name, nodes,
                           amplitude=230.0 * math.sqrt(2),
                           frequency=50.0, **kw)


def AC120V_60Hz(name: str, nodes: tuple[Node, Node], **kw) -> VoltageSource:
    """120 V RMS, 60 Hz US mains supply (peak ≈ 169.7 V).

    ``nodes = (positive, negative)``
    """
    return ACVoltageSource(name, nodes,
                           amplitude=120.0 * math.sqrt(2),
                           frequency=60.0, **kw)


def AC100V_50Hz(name: str, nodes: tuple[Node, Node], **kw) -> VoltageSource:
    """100 V RMS, 50 Hz Japan-East mains supply (peak ≈ 141.4 V).

    ``nodes = (positive, negative)``
    """
    return ACVoltageSource(name, nodes,
                           amplitude=100.0 * math.sqrt(2),
                           frequency=50.0, **kw)
