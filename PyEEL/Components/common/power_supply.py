"""Power supply building blocks — DC/AC supplies, linear PSU, transformer PSU."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...Core.Node import Node
from ..Passive.Resistor import Resistor
from ..Passive.Capacitor import Capacitor
from ..Magnetic.Transformer import Transformer
from ..Sources.VoltageSource import DCVoltageSource, ACVoltageSource
from .diode_circuits import full_bridge_rectifier

if TYPE_CHECKING:
    from ..Component import Component


def dc_supply(
    prefix: str,
    n_vcc: Node,
    n_gnd: Node,
    *,
    voltage: float,
) -> list[Component]:
    """
    Simple DC supply: a :class:`DCVoltageSource` between two nodes.

    Returns ``[V_dc]``.
    """
    return [DCVoltageSource(f"{prefix}_V", (n_vcc, n_gnd), voltage=voltage)]


def ac_supply(
    prefix: str,
    n_out: Node,
    n_gnd: Node,
    *,
    amplitude: float,
    frequency: float,
) -> list[Component]:
    """
    Simple AC supply: an :class:`ACVoltageSource`.

    Returns ``[V_ac]``.
    """
    return [ACVoltageSource(f"{prefix}_V", (n_out, n_gnd),
                            amplitude=amplitude, frequency=frequency)]


def linear_power_supply(
    prefix: str,
    node_manager,
    n_ac_p: Node,
    n_ac_n: Node,
    n_dc_out: Node,
    n_gnd: Node,
    *,
    r_load: float,
    c_filter: float = 1000e-6,
    Is: float = 1e-14,
) -> tuple[list[Component], dict[str, Node]]:
    """
    Full-bridge rectifier + filter capacitor + load resistor.

    ::

        n_ac_p ──┐          ┌── n_dc_out ──┬── R_load ── n_gnd
                 Bridge                    C_filter
        n_ac_n ──┘          └── n_dc_neg ──┘

    Typically driven by a transformer secondary.

    Returns ``(components, {'dc_neg'})``.
    """
    n_dc_neg = node_manager.AddNode(f"{prefix}_dc_neg")

    bridge = full_bridge_rectifier(
        f"{prefix}_bridge", n_ac_p, n_ac_n, n_dc_out, n_dc_neg, Is=Is,
    )

    comps: list[Component] = [
        *bridge,
        Capacitor(f"{prefix}_C_filt", (n_dc_out, n_gnd), capacitance=c_filter),
        Resistor(f"{prefix}_R_load", (n_dc_out, n_gnd), resistance=r_load),
        Resistor(f"{prefix}_R_gnd", (n_dc_neg, n_gnd), resistance=0.01),
    ]
    return comps, {"dc_neg": n_dc_neg}


def transformer_supply(
    prefix: str,
    node_manager,
    n_mains_p: Node,
    n_mains_n: Node,
    n_dc_out: Node,
    n_gnd: Node,
    *,
    primary_inductance: float = 100.0,
    secondary_inductance: float = 1.0,
    k: float = 0.999,
    r_load: float = 100.0,
    c_filter: float = 1000e-6,
    r_primary_gnd: float = 0.01,
    Is: float = 1e-14,
) -> tuple[list[Component], dict[str, Node]]:
    """
    Complete linear power supply: transformer + bridge rectifier +
    filter cap + load.

    ::

        n_mains_p ──┐           ┌── bridge ── n_dc_out ──┬── R_load ── n_gnd
                    Transformer                          C_filter
        n_mains_n ──┘           └──────────── dc_neg ────┘

    Returns ``(components, {'sec_p', 'sec_n', 'dc_neg'})``.
    """
    n_sec_p = node_manager.AddNode(f"{prefix}_sec_p")
    n_sec_n = node_manager.AddNode(f"{prefix}_sec_n")

    prim_gnd_r = Resistor(
        f"{prefix}_R_prim_gnd", (n_mains_n, n_gnd), resistance=r_primary_gnd,
    )

    xfmr = Transformer(
        f"{prefix}_T",
        primary_nodes=(n_mains_p, n_mains_n),
        secondary_nodes=(n_sec_p, n_sec_n),
        primary_inductance=primary_inductance,
        secondary_inductance=secondary_inductance,
        k=k,
    )

    psu_comps, psu_nodes = linear_power_supply(
        f"{prefix}_psu", node_manager,
        n_sec_p, n_sec_n, n_dc_out, n_gnd,
        r_load=r_load, c_filter=c_filter, Is=Is,
    )

    comps: list[Component] = [prim_gnd_r, xfmr, *psu_comps]
    internal = {
        "sec_p": n_sec_p,
        "sec_n": n_sec_n,
        **psu_nodes,
    }
    return comps, internal
