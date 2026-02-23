"""Passive network building blocks — voltage dividers, filters, etc."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...Core.Node import Node
from ..Passive.Resistor import Resistor
from ..Passive.Capacitor import Capacitor
from ..Passive.Inductor import Inductor

if TYPE_CHECKING:
    from ..Component import Component


def voltage_divider(
    prefix: str,
    n_in: Node,
    n_out: Node,
    n_gnd: Node,
    *,
    r_top: float,
    r_bottom: float,
) -> list[Component]:
    """
    Resistive voltage divider.

    ::

        n_in ── R_top ── n_out ── R_bottom ── n_gnd

    ``V(n_out) ≈ V(n_in) × R_bottom / (R_top + R_bottom)``

    Returns ``[R_top, R_bottom]``.
    """
    return [
        Resistor(f"{prefix}_R_top", (n_in, n_out), resistance=r_top),
        Resistor(f"{prefix}_R_bot", (n_out, n_gnd), resistance=r_bottom),
    ]


def rc_low_pass(
    prefix: str,
    n_in: Node,
    n_out: Node,
    n_gnd: Node,
    *,
    resistance: float,
    capacitance: float,
) -> list[Component]:
    """
    First-order RC low-pass filter.

    ::

        n_in ── R ── n_out ── C ── n_gnd

    Cutoff: ``f_c = 1 / (2π · R · C)``

    Returns ``[R, C]``.
    """
    return [
        Resistor(f"{prefix}_R", (n_in, n_out), resistance=resistance),
        Capacitor(f"{prefix}_C", (n_out, n_gnd), capacitance=capacitance),
    ]


def rc_high_pass(
    prefix: str,
    n_in: Node,
    n_out: Node,
    n_gnd: Node,
    *,
    resistance: float,
    capacitance: float,
) -> list[Component]:
    """
    First-order RC high-pass filter.

    ::

        n_in ── C ── n_out ── R ── n_gnd

    Cutoff: ``f_c = 1 / (2π · R · C)``

    Returns ``[C, R]``.
    """
    return [
        Capacitor(f"{prefix}_C", (n_in, n_out), capacitance=capacitance),
        Resistor(f"{prefix}_R", (n_out, n_gnd), resistance=resistance),
    ]


def series_lcr(
    prefix: str,
    n_in: Node,
    n_L_out: Node,
    n_C_out: Node,
    n_gnd: Node,
    *,
    inductance: float,
    capacitance: float,
    resistance: float,
) -> list[Component]:
    """
    Series LCR network.

    ::

        n_in ── L ── n_L_out ── C ── n_C_out ── R ── n_gnd

    Resonant frequency: ``f₀ = 1 / (2π√(LC))``

    Returns ``[L, C, R]``.
    """
    return [
        Inductor(f"{prefix}_L", (n_in, n_L_out), inductance=inductance),
        Capacitor(f"{prefix}_C", (n_L_out, n_C_out), capacitance=capacitance),
        Resistor(f"{prefix}_R", (n_C_out, n_gnd), resistance=resistance),
    ]


def parallel_rc(
    prefix: str,
    n_pos: Node,
    n_neg: Node,
    *,
    resistance: float,
    capacitance: float,
) -> list[Component]:
    """
    Parallel RC load (e.g. filter cap + load resistor).

    ::

        n_pos ──┬── R ──┬── n_neg
                └── C ──┘

    Returns ``[R, C]``.
    """
    return [
        Resistor(f"{prefix}_R", (n_pos, n_neg), resistance=resistance),
        Capacitor(f"{prefix}_C", (n_pos, n_neg), capacitance=capacitance),
    ]
