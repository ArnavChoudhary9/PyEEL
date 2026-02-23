"""Utility helpers for common circuit operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..Component import Component


def add_all(circuit, components: list[Component]) -> None:
    """
    Convenience: call ``circuit.AddComponent(c)`` for every component
    in *components*.
    """
    for c in components:
        circuit.AddComponent(c)
