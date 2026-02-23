"""Diode-based circuit building blocks — rectifiers, clamps, regulators."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...Core.Node import Node
from ..Passive.Resistor import Resistor
from ..Semiconductors.Diode import Diode
from ..Semiconductors.ZenerDiode import ZenerDiode

if TYPE_CHECKING:
    from ..Component import Component


def half_wave_rectifier(
    prefix: str,
    n_ac: Node,
    n_dc: Node,
    n_gnd: Node,
    *,
    r_load: float,
    Is: float = 1e-14,
    n_diode: float = 1.0,
) -> list[Component]:
    """
    Half-wave rectifier: diode + load resistor.

    ::

        n_ac ──▷|── n_dc ── R_load ── n_gnd

    Returns ``[D, R_load]``.
    """
    return [
        Diode(f"{prefix}_D", (n_ac, n_dc), Is=Is, n=n_diode),
        Resistor(f"{prefix}_R_load", (n_dc, n_gnd), resistance=r_load),
    ]


def full_bridge_rectifier(
    prefix: str,
    n_ac_p: Node,
    n_ac_n: Node,
    n_dc_p: Node,
    n_dc_n: Node,
    *,
    Is: float = 1e-14,
    n_diode: float = 1.0,
) -> list[Component]:
    """
    Full-wave bridge rectifier (4 diodes).

    ::

        n_ac_p ──▷|── n_dc_p        n_dc_n ──▷|── n_ac_p
        n_ac_n ──▷|── n_dc_p        n_dc_n ──▷|── n_ac_n

    Connect a load between ``n_dc_p`` and ``n_dc_n`` externally.

    Returns ``[D1, D2, D3, D4]``.
    """
    kw = dict(Is=Is, n=n_diode)
    return [
        Diode(f"{prefix}_D1", (n_ac_p, n_dc_p), **kw),
        Diode(f"{prefix}_D2", (n_ac_n, n_dc_p), **kw),
        Diode(f"{prefix}_D3", (n_dc_n, n_ac_p), **kw),
        Diode(f"{prefix}_D4", (n_dc_n, n_ac_n), **kw),
    ]


def zener_clamp(
    prefix: str,
    n_in: Node,
    n_out: Node,
    n_gnd: Node,
    *,
    r_series: float,
    Vz: float = 5.1,
    Is: float = 1e-14,
) -> list[Component]:
    """
    Zener clamp / clipper: series resistor + Zener to ground.

    ::

        n_in ── R_series ── n_out
                              │
                             DZ (cathode up)
                              │
                            n_gnd

    Clips ``V(n_out)`` at approximately ±Vz.

    Returns ``[R_series, DZ]``.
    """
    return [
        Resistor(f"{prefix}_R", (n_in, n_out), resistance=r_series),
        ZenerDiode(f"{prefix}_DZ", (n_gnd, n_out), Vz=Vz, Is=Is),
    ]


def zener_regulator(
    prefix: str,
    n_in: Node,
    n_out: Node,
    n_gnd: Node,
    *,
    r_series: float,
    r_load: float,
    Vz: float = 5.1,
    Is: float = 1e-14,
) -> list[Component]:
    """
    Zener shunt regulator: series R + Zener + parallel load.

    ::

        n_in ── R_series ── n_out ── R_load ── n_gnd
                              │
                             DZ (cathode at n_out, anode at n_gnd)
                              │
                            n_gnd

    Regulates ``V(n_out) ≈ Vz`` as long as series current is sufficient.

    Returns ``[R_series, DZ, R_load]``.
    """
    return [
        Resistor(f"{prefix}_R", (n_in, n_out), resistance=r_series),
        ZenerDiode(f"{prefix}_DZ", (n_gnd, n_out), Vz=Vz, Is=Is),
        Resistor(f"{prefix}_R_load", (n_out, n_gnd), resistance=r_load),
    ]
