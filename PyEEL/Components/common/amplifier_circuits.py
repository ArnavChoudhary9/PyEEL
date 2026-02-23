"""Transistor amplifier stages — CE, common-source, etc."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...Core.Node import Node
from ..Passive.Resistor import Resistor
from ..Passive.Capacitor import Capacitor
from ..Semiconductors.BJT import BJTType, NPN as _NPN, PNP as _PNP
from ..Semiconductors.MOSFET import MOSFETType, NMOS as _NMOS, PMOS as _PMOS

if TYPE_CHECKING:
    from ..Component import Component


def ce_amplifier(
    prefix: str,
    n_vcc: Node,
    n_in: Node,
    n_out: Node,
    n_gnd: Node,
    *,
    r_collector: float = 4.7e3,
    r_emitter: float = 1e3,
    r_bias_top: float = 56e3,
    r_bias_bottom: float = 12e3,
    bjt_type: str = "NPN",
    bjt_params: dict | None = None,
) -> tuple[list[Component], dict[str, Node]]:
    """
    Voltage-divider-biased common-emitter amplifier (simplified).

    Uses ``n_in`` as the base node and ``n_out`` as the collector.
    Emitter connects directly to ground (no R_E).
    For a full CE amp with R_E, use :func:`ce_amplifier_with_nodes`.

    ::

        n_vcc ── R_bias_top ── n_in (base)
        n_in ── R_bias_bottom ── n_gnd
        n_vcc ── R_collector ── n_out (collector)
        BJT: (n_out, n_in, n_gnd)

    Returns ``(components, {})``.
    """
    params = bjt_params or {}
    if bjt_type.upper() == "NPN":
        Q = _NPN(f"{prefix}_Q", (n_out, n_in, n_gnd), **params)
    else:
        Q = _PNP(f"{prefix}_Q", (n_out, n_in, n_gnd), **params)

    return [
        Resistor(f"{prefix}_Rc", (n_vcc, n_out), resistance=r_collector),
        Resistor(f"{prefix}_Rb_top", (n_vcc, n_in), resistance=r_bias_top),
        Resistor(f"{prefix}_Rb_bot", (n_in, n_gnd), resistance=r_bias_bottom),
        Q,
    ], {}


def ce_amplifier_with_nodes(
    prefix: str,
    node_manager,
    n_vcc: Node,
    n_in: Node,
    n_out: Node,
    n_gnd: Node,
    *,
    r1: float = 56e3,
    r2: float = 12e3,
    rc: float = 4.7e3,
    re: float = 1e3,
    c_in: float = 10e-6,
    c_out: float = 10e-6,
    BF: float = 100.0,
    Is: float = 1e-15,
    Vaf: float | None = None,
) -> tuple[list[Component], dict[str, Node]]:
    """
    Voltage-divider–biased common-emitter NPN amplifier.

    Unlike :func:`ce_amplifier`, this variant takes a *node_manager*
    so it can create the internal base/collector/emitter nodes itself.

    ::

             VCC
              │       │
             R1      RC
              │       │
         n_b ─┤  Q1  ├─ n_c ── C_out ── n_out
              │       │
             R2      RE
              │       │
             GND     GND

        n_in ── C_in ── n_b

    Returns ``(components, {'base', 'collector', 'emitter'})``.
    """
    n_b = node_manager.AddNode(f"{prefix}_base")
    n_c = node_manager.AddNode(f"{prefix}_collector")
    n_e = node_manager.AddNode(f"{prefix}_emitter")

    comps: list[Component] = [
        Resistor(f"{prefix}_R1", (n_vcc, n_b), resistance=r1),
        Resistor(f"{prefix}_R2", (n_b, n_gnd), resistance=r2),
        _NPN(f"{prefix}_Q", (n_c, n_b, n_e), BF=BF, Is=Is, Vaf=Vaf),
        Resistor(f"{prefix}_RC", (n_vcc, n_c), resistance=rc),
        Resistor(f"{prefix}_RE", (n_e, n_gnd), resistance=re),
        Capacitor(f"{prefix}_C_in", (n_in, n_b), capacitance=c_in),
        Capacitor(f"{prefix}_C_out", (n_c, n_out), capacitance=c_out),
    ]

    internal = {"base": n_b, "collector": n_c, "emitter": n_e}
    return comps, internal


def common_source_amplifier(
    prefix: str,
    node_manager,
    n_vdd: Node,
    n_in: Node,
    n_out: Node,
    n_gnd: Node,
    *,
    rd: float = 10e3,
    rs: float = 1e3,
    rg: float = 1e6,
    c_in: float = 1e-6,
    c_out: float = 1e-6,
    Kp: float = 2e-5,
    Vth: float = 1.0,
    lambda_: float = 0.0,
    mosfet_type: MOSFETType = MOSFETType.NMOS,
) -> tuple[list[Component], dict[str, Node]]:
    """
    Self-biased common-source MOSFET amplifier.

    ::

             VDD
              │
             RD
              │
         n_d ─┤  M1  ├─ n_s ── RS ── GND
              gate
              │
        n_in ── C_in ── gate ── RG ── GND
                          n_d ── C_out ── n_out

    Returns ``(components, {'drain', 'gate', 'source'})``.
    """
    n_g = node_manager.AddNode(f"{prefix}_gate")
    n_d = node_manager.AddNode(f"{prefix}_drain")
    n_s = node_manager.AddNode(f"{prefix}_source")

    mosfet_factory = _NMOS if mosfet_type == MOSFETType.NMOS else _PMOS
    comps: list[Component] = [
        Resistor(f"{prefix}_RG", (n_g, n_gnd), resistance=rg),
        mosfet_factory(f"{prefix}_M", (n_d, n_g, n_s),
                       Kp=Kp, Vth=Vth, lambda_=lambda_),
        Resistor(f"{prefix}_RD", (n_vdd, n_d), resistance=rd),
        Resistor(f"{prefix}_RS", (n_s, n_gnd), resistance=rs),
        Capacitor(f"{prefix}_C_in", (n_in, n_g), capacitance=c_in),
        Capacitor(f"{prefix}_C_out", (n_d, n_out), capacitance=c_out),
    ]

    internal = {"drain": n_d, "gate": n_g, "source": n_s}
    return comps, internal
