"""
Common circuit building blocks — factory helpers.

Each function creates a small *sub-circuit* of pre-connected
components and returns them as a list that can be added to a
:class:`~PyEEL.Simulation.Circuit.Circuit` in one shot.

Usage::

    from PyEEL.Components.common import voltage_divider

    ckt = Circuit(solver=NumpySolver())
    nm  = ckt.NodeManager
    gnd = nm.GroundNode
    n_in  = nm.AddNode("n_in")
    n_out = nm.AddNode("n_out")

    for comp in voltage_divider("bias", n_in, n_out, gnd,
                                r_top=56e3, r_bottom=12e3):
        ckt.AddComponent(comp)

Every helper returns ``list[Component]`` so callers always have a
uniform integration pattern.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ..Core.Node import Node

# ── Passive ─────────────────────────────────────────────────────────
from .Passive.Resistor import Resistor
from .Passive.Capacitor import Capacitor
from .Passive.Inductor import Inductor

# ── Semiconductors ──────────────────────────────────────────────────
from .Semiconductors.Diode import Diode
from .Semiconductors.ZenerDiode import ZenerDiode
from .Semiconductors.BJT import BJT, BJTType, NPN as _NPN, PNP as _PNP
from .Semiconductors.MOSFET import MOSFET, MOSFETType, NMOS as _NMOS, PMOS as _PMOS

# ── Magnetic ────────────────────────────────────────────────────────
from .Magnetic.Transformer import Transformer

# ── Sources ─────────────────────────────────────────────────────────
from .Sources.VoltageSource import (
    VoltageSource, DCVoltageSource, ACVoltageSource,
)

# ── ICs ─────────────────────────────────────────────────────────────
from .ICs.OpAmp import OpAmp

if TYPE_CHECKING:
    from .Component import Component


# =====================================================================
#  Passive Networks
# =====================================================================

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


# =====================================================================
#  Diode Circuits
# =====================================================================

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


# =====================================================================
#  Transistor Stages
# =====================================================================

def ce_amplifier(
    prefix: str,
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

    Creates internal nodes for base, collector, and emitter.

    ::

             VCC
              │       │
             R1      RC
              │       │
              ├── Q ──┤── C_out ── n_out
              │       │
             R2      RE
              │       │
             GND     GND

        n_in ── C_in ── base

    Returns
    -------
    (components, internal_nodes)
        *components* is the list to add to the circuit.
        *internal_nodes* is a dict with keys ``'base'``, ``'collector'``,
        ``'emitter'`` holding the :class:`Node` objects created by
        this helper (useful for attaching probes).

    .. note::
       You must create the nodes through the circuit's NodeManager
       **before** calling this helper.  Pass them in via
       ``n_vcc``, ``n_in``, ``n_out``, ``n_gnd``.  Internal base /
       collector / emitter nodes are created automatically through
       the same NodeManager — call the returned ``internal_nodes``
       to obtain references.
    """
    # We need internal nodes — caller is expected to get them from
    # the NodeManager first, so we use the _NodeManager hack here.
    # Instead, require them to be provided OR we take a NodeManager.
    # For simplicity: require the caller to pass them.
    raise _NeedInternalNodesError(
        "ce_amplifier requires internal nodes. Use ce_amplifier_with_nodes() instead."
    )


class _NeedInternalNodesError(Exception):
    pass


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

    Parameters
    ----------
    prefix : str
        Name prefix for all generated components (e.g. ``"amp"``).
    node_manager
        The circuit's NodeManager (``circuit.NodeManager``).
    n_vcc : Node
        Supply rail node (connect a DC source externally).
    n_in : Node
        AC input node (signal enters here).
    n_out : Node
        AC output node (signal leaves here).
    n_gnd : Node
        Ground reference.
    r1, r2 : float
        Bias-divider resistors (Ω).
    rc : float
        Collector resistor (Ω).
    re : float
        Emitter resistor (Ω).
    c_in, c_out : float
        Input/output coupling capacitors (F).
    BF : float
        BJT forward current gain.
    Is : float
        BJT saturation current (A).
    Vaf : float | None
        Early voltage (V); ``None`` disables the Early effect.

    Returns
    -------
    (components, internal_nodes)
        *components* — list to feed to ``circuit.AddComponent()``.
        *internal_nodes* — ``{'base': …, 'collector': …, 'emitter': …}``.
    """
    n_b = node_manager.AddNode(f"{prefix}_base")
    n_c = node_manager.AddNode(f"{prefix}_collector")
    n_e = node_manager.AddNode(f"{prefix}_emitter")

    comps: list[Component] = [
        # Bias divider
        Resistor(f"{prefix}_R1", (n_vcc, n_b), resistance=r1),
        Resistor(f"{prefix}_R2", (n_b, n_gnd), resistance=r2),
        # Transistor
        _NPN(f"{prefix}_Q", (n_c, n_b, n_e), BF=BF, Is=Is, Vaf=Vaf),
        # Collector & emitter resistors
        Resistor(f"{prefix}_RC", (n_vcc, n_c), resistance=rc),
        Resistor(f"{prefix}_RE", (n_e, n_gnd), resistance=re),
        # Coupling caps
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

    Parameters
    ----------
    prefix : str
        Name prefix for all generated components.
    node_manager
        The circuit's NodeManager.
    n_vdd : Node
        Supply rail node.
    n_in : Node
        AC input node.
    n_out : Node
        AC output node.
    n_gnd : Node
        Ground reference.
    rd : float
        Drain resistor (Ω).
    rs : float
        Source resistor (Ω).
    rg : float
        Gate bias resistor to ground (Ω).
    c_in, c_out : float
        Input/output coupling capacitors (F).
    Kp, Vth, lambda\\_ : float
        MOSFET model parameters.
    mosfet_type : MOSFETType
        NMOS or PMOS.  Default NMOS.

    Returns
    -------
    (components, internal_nodes)
        *internal_nodes* keys: ``'drain'``, ``'gate'``, ``'source'``.
    """
    n_g = node_manager.AddNode(f"{prefix}_gate")
    n_d = node_manager.AddNode(f"{prefix}_drain")
    n_s = node_manager.AddNode(f"{prefix}_source")

    mosfet_factory = _NMOS if mosfet_type == MOSFETType.NMOS else _PMOS
    comps: list[Component] = [
        # Gate bias
        Resistor(f"{prefix}_RG", (n_g, n_gnd), resistance=rg),
        # MOSFET
        mosfet_factory(f"{prefix}_M", (n_d, n_g, n_s),
                       Kp=Kp, Vth=Vth, lambda_=lambda_),
        # Drain & source resistors
        Resistor(f"{prefix}_RD", (n_vdd, n_d), resistance=rd),
        Resistor(f"{prefix}_RS", (n_s, n_gnd), resistance=rs),
        # Coupling caps
        Capacitor(f"{prefix}_C_in", (n_in, n_g), capacitance=c_in),
        Capacitor(f"{prefix}_C_out", (n_d, n_out), capacitance=c_out),
    ]

    internal = {"drain": n_d, "gate": n_g, "source": n_s}
    return comps, internal


# =====================================================================
#  Power Supplies
# =====================================================================

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

    Parameters
    ----------
    prefix : str
        Name prefix for all generated components.
    node_manager
        The circuit's NodeManager.
    n_ac_p, n_ac_n : Node
        AC input from the transformer secondary.
    n_dc_out : Node
        Positive DC output.
    n_gnd : Node
        Ground / DC negative rail.
    r_load : float
        Load resistance (Ω).
    c_filter : float
        Filter capacitor (F).  Default 1000 µF.
    Is : float
        Bridge diode saturation current (A).

    Returns
    -------
    (components, internal_nodes)
        *internal_nodes* keys: ``'dc_neg'``.
    """
    n_dc_neg = node_manager.AddNode(f"{prefix}_dc_neg")

    bridge = full_bridge_rectifier(
        f"{prefix}_bridge", n_ac_p, n_ac_n, n_dc_out, n_dc_neg, Is=Is,
    )

    comps: list[Component] = [
        *bridge,
        Capacitor(f"{prefix}_C_filt", (n_dc_out, n_gnd), capacitance=c_filter),
        Resistor(f"{prefix}_R_load", (n_dc_out, n_gnd), resistance=r_load),
        # Tie bridge negative rail to ground
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

    Parameters
    ----------
    prefix : str
        Name prefix.
    node_manager
        The circuit's NodeManager.
    n_mains_p, n_mains_n : Node
        Primary (mains) supply nodes.
    n_dc_out : Node
        Positive DC output node.
    n_gnd : Node
        Ground reference.
    primary_inductance, secondary_inductance : float
        Winding inductances (H).  Turns ratio ≈
        ``√(L_primary / L_secondary)``.
    k : float
        Coupling coefficient (< 1).  Default 0.999.
    r_load : float
        Output load (Ω).
    c_filter : float
        Filter capacitance (F).
    r_primary_gnd : float
        Small resistor tying primary return to ground (Ω).
    Is : float
        Bridge diode saturation current (A).

    Returns
    -------
    (components, internal_nodes)
        Keys: ``'sec_p'``, ``'sec_n'``, ``'dc_neg'``.
    """
    n_sec_p = node_manager.AddNode(f"{prefix}_sec_p")
    n_sec_n = node_manager.AddNode(f"{prefix}_sec_n")

    # Primary return to ground (avoids floating node)
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


# =====================================================================
#  Utility
# =====================================================================

def add_all(circuit, components: list[Component]) -> None:
    """
    Convenience: call ``circuit.AddComponent(c)`` for every component
    in *components*.
    """
    for c in components:
        circuit.AddComponent(c)


# =====================================================================
#  Op-Amp Circuits
# =====================================================================

def inverting_amplifier(
    prefix: str,
    node_manager,
    n_in: Node,
    n_out: Node,
    n_gnd: Node,
    *,
    r_in: float = 10e3,
    r_f: float = 100e3,
    A_OL: float = 200_000.0,
    R_in_opamp: float = 2e6,
    R_out_opamp: float = 75.0,
) -> tuple[list[Component], dict[str, Node]]:
    """
    Inverting amplifier.

    ::

                  R_f
             ┌────┤────┐
             │         │
        n_in ── R_in ──┤(−)      │
                       │   U  ├──┘── n_out
                   n_gnd──(+)

    Gain ≈ ``−R_f / R_in``

    Parameters
    ----------
    prefix : str
        Name prefix for all generated components.
    node_manager
        The circuit's NodeManager.
    n_in : Node
        Signal input node.
    n_out : Node
        Amplifier output node.
    n_gnd : Node
        Ground reference (connects to non-inverting input).
    r_in : float
        Input resistor (Ω).  Default 10 kΩ.
    r_f : float
        Feedback resistor (Ω).  Default 100 kΩ.
    A_OL, R_in_opamp, R_out_opamp : float
        Op-amp model parameters.

    Returns
    -------
    (components, internal_nodes)
        *internal_nodes* keys: ``'inv_input'``.
    """
    n_inv = node_manager.AddNode(f"{prefix}_inv")

    comps: list[Component] = [
        Resistor(f"{prefix}_Rin", (n_in, n_inv), resistance=r_in),
        Resistor(f"{prefix}_Rf", (n_inv, n_out), resistance=r_f),
        OpAmp(f"{prefix}_U", (n_gnd, n_inv, n_out),
              A_OL=A_OL, R_in=R_in_opamp, R_out=R_out_opamp),
    ]
    return comps, {"inv_input": n_inv}


def non_inverting_amplifier(
    prefix: str,
    node_manager,
    n_in: Node,
    n_out: Node,
    n_gnd: Node,
    *,
    r1: float = 10e3,
    r_f: float = 90e3,
    A_OL: float = 200_000.0,
    R_in_opamp: float = 2e6,
    R_out_opamp: float = 75.0,
) -> tuple[list[Component], dict[str, Node]]:
    """
    Non-inverting amplifier.

    ::

        n_in ──(+)       │
                   U  ├──┘── n_out
               ┌──(−)       │
               │             │
               ├──── R_f ────┘
               │
               └──── R1 ──── n_gnd

    Gain ≈ ``1 + R_f / R1``

    Parameters
    ----------
    prefix : str
        Name prefix.
    node_manager
        The circuit's NodeManager.
    n_in : Node
        Signal input node (connects to non-inverting input).
    n_out : Node
        Amplifier output node.
    n_gnd : Node
        Ground reference.
    r1 : float
        Ground resistor (Ω).  Default 10 kΩ.
    r_f : float
        Feedback resistor (Ω).  Default 90 kΩ.  Gain = 1 + Rf/R1 = 10.
    A_OL, R_in_opamp, R_out_opamp : float
        Op-amp model parameters.

    Returns
    -------
    (components, internal_nodes)
        *internal_nodes* keys: ``'inv_input'``.
    """
    n_inv = node_manager.AddNode(f"{prefix}_inv")

    comps: list[Component] = [
        Resistor(f"{prefix}_R1", (n_inv, n_gnd), resistance=r1),
        Resistor(f"{prefix}_Rf", (n_inv, n_out), resistance=r_f),
        OpAmp(f"{prefix}_U", (n_in, n_inv, n_out),
              A_OL=A_OL, R_in=R_in_opamp, R_out=R_out_opamp),
    ]
    return comps, {"inv_input": n_inv}


def voltage_follower(
    prefix: str,
    node_manager,
    n_in: Node,
    n_out: Node,
    *,
    A_OL: float = 200_000.0,
    R_in_opamp: float = 2e6,
    R_out_opamp: float = 75.0,
) -> tuple[list[Component], dict[str, Node]]:
    """
    Unity-gain voltage follower (buffer).

    ::

        n_in ──(+)       │
                   U  ├──┘── n_out
               ┌──(−)       │
               └─────────────┘  (wire feedback)

    Gain = 1.  Very high input impedance, very low output impedance.

    A tiny "wire" resistor (0.001 Ω) models the direct feedback
    connection from output to inverting input.

    Returns
    -------
    (components, internal_nodes)
        *internal_nodes* keys: ``'feedback'``.
    """
    n_fb = node_manager.AddNode(f"{prefix}_fb")
    comps: list[Component] = [
        Resistor(f"{prefix}_Rwire", (n_out, n_fb), resistance=0.001),
        OpAmp(f"{prefix}_U", (n_in, n_fb, n_out),
              A_OL=A_OL, R_in=R_in_opamp, R_out=R_out_opamp),
    ]
    return comps, {"feedback": n_fb}


def summing_amplifier(
    prefix: str,
    node_manager,
    input_nodes: list[Node],
    n_out: Node,
    n_gnd: Node,
    *,
    r_inputs: list[float] | float = 10e3,
    r_f: float = 10e3,
    A_OL: float = 200_000.0,
    R_in_opamp: float = 2e6,
    R_out_opamp: float = 75.0,
) -> tuple[list[Component], dict[str, Node]]:
    """
    Inverting summing amplifier (N inputs).

    ::

        n_1 ── R1 ──┐
        n_2 ── R2 ──┤(−)      │
        ...         │   U  ├──┘── n_out
                n_gnd──(+)
                (−)── R_f ── n_out

    If all input resistors equal:
    ``V_out ≈ −(R_f / R_in) · (V_1 + V_2 + … + V_N)``

    Parameters
    ----------
    prefix : str
        Name prefix.
    node_manager
        The circuit's NodeManager.
    input_nodes : list[Node]
        Input signal nodes.
    n_out : Node
        Output node.
    n_gnd : Node
        Ground reference.
    r_inputs : list[float] | float
        Input resistor(s).  A single float applies to all inputs.
    r_f : float
        Feedback resistor (Ω).
    A_OL, R_in_opamp, R_out_opamp : float
        Op-amp model parameters.

    Returns
    -------
    (components, internal_nodes)
        *internal_nodes* keys: ``'summing_junction'``.
    """
    n_sum = node_manager.AddNode(f"{prefix}_sum")

    if isinstance(r_inputs, (int, float)):
        r_list = [float(r_inputs)] * len(input_nodes)
    else:
        r_list = list(r_inputs)
    if len(r_list) != len(input_nodes):
        raise ValueError("r_inputs length must match input_nodes length.")

    comps: list[Component] = []
    for i, (n_i, r_i) in enumerate(zip(input_nodes, r_list)):
        comps.append(Resistor(f"{prefix}_R{i+1}", (n_i, n_sum), resistance=r_i))
    comps.append(Resistor(f"{prefix}_Rf", (n_sum, n_out), resistance=r_f))
    comps.append(
        OpAmp(f"{prefix}_U", (n_gnd, n_sum, n_out),
              A_OL=A_OL, R_in=R_in_opamp, R_out=R_out_opamp),
    )
    return comps, {"summing_junction": n_sum}


def difference_amplifier(
    prefix: str,
    node_manager,
    n_in_pos: Node,
    n_in_neg: Node,
    n_out: Node,
    n_gnd: Node,
    *,
    r1: float = 10e3,
    r2: float = 10e3,
    r3: float = 10e3,
    r_f: float = 10e3,
    A_OL: float = 200_000.0,
    R_in_opamp: float = 2e6,
    R_out_opamp: float = 75.0,
) -> tuple[list[Component], dict[str, Node]]:
    """
    Difference (differential) amplifier.

    ::

        n_in_neg ── R1 ──┤(−)          │
                          │    U  ├─────┘── n_out
        n_in_pos ── R3 ──┤(+)          │
                          │             │
                         R2 ── GND      │
                  (−)──── R_f ──────────┘

    When ``R1 = R3`` and ``R2 = R_f``:
    ``V_out = (R_f / R1) · (V_pos − V_neg)``

    Parameters
    ----------
    prefix : str
        Name prefix.
    node_manager
        The circuit's NodeManager.
    n_in_pos, n_in_neg : Node
        Positive and negative signal inputs.
    n_out : Node
        Output node.
    n_gnd : Node
        Ground reference.
    r1 : float
        Resistor from negative input to inverting pin (Ω).
    r2 : float
        Resistor from non-inverting pin to ground (Ω).
    r3 : float
        Resistor from positive input to non-inverting pin (Ω).
    r_f : float
        Feedback resistor from output to inverting pin (Ω).
    A_OL, R_in_opamp, R_out_opamp : float
        Op-amp model parameters.

    Returns
    -------
    (components, internal_nodes)
        *internal_nodes* keys: ``'inv_input'``, ``'noninv_input'``.
    """
    n_inv = node_manager.AddNode(f"{prefix}_inv")
    n_ni = node_manager.AddNode(f"{prefix}_ni")

    comps: list[Component] = [
        Resistor(f"{prefix}_R1", (n_in_neg, n_inv), resistance=r1),
        Resistor(f"{prefix}_Rf", (n_inv, n_out), resistance=r_f),
        Resistor(f"{prefix}_R3", (n_in_pos, n_ni), resistance=r3),
        Resistor(f"{prefix}_R2", (n_ni, n_gnd), resistance=r2),
        OpAmp(f"{prefix}_U", (n_ni, n_inv, n_out),
              A_OL=A_OL, R_in=R_in_opamp, R_out=R_out_opamp),
    ]
    return comps, {"inv_input": n_inv, "noninv_input": n_ni}


def integrator(
    prefix: str,
    node_manager,
    n_in: Node,
    n_out: Node,
    n_gnd: Node,
    *,
    r_in: float = 10e3,
    c_f: float = 100e-9,
    A_OL: float = 200_000.0,
    R_in_opamp: float = 2e6,
    R_out_opamp: float = 75.0,
) -> tuple[list[Component], dict[str, Node]]:
    """
    Inverting integrator.

    ::

                  C_f
             ┌────┤────┐
             │         │
        n_in ── R_in ──┤(−)      │
                       │   U  ├──┘── n_out
                   n_gnd──(+)

    ``V_out(t) = −(1/RC) ∫ V_in dt``

    Parameters
    ----------
    prefix : str
        Name prefix.
    node_manager
        The circuit's NodeManager.
    n_in : Node
        Input node.
    n_out : Node
        Output node.
    n_gnd : Node
        Ground reference.
    r_in : float
        Input resistor (Ω).
    c_f : float
        Feedback capacitor (F).
    A_OL, R_in_opamp, R_out_opamp : float
        Op-amp model parameters.

    Returns
    -------
    (components, internal_nodes)
        *internal_nodes* keys: ``'inv_input'``.
    """
    n_inv = node_manager.AddNode(f"{prefix}_inv")

    comps: list[Component] = [
        Resistor(f"{prefix}_Rin", (n_in, n_inv), resistance=r_in),
        Capacitor(f"{prefix}_Cf", (n_inv, n_out), capacitance=c_f),
        OpAmp(f"{prefix}_U", (n_gnd, n_inv, n_out),
              A_OL=A_OL, R_in=R_in_opamp, R_out=R_out_opamp),
    ]
    return comps, {"inv_input": n_inv}


def differentiator(
    prefix: str,
    node_manager,
    n_in: Node,
    n_out: Node,
    n_gnd: Node,
    *,
    c_in: float = 100e-9,
    r_f: float = 10e3,
    A_OL: float = 200_000.0,
    R_in_opamp: float = 2e6,
    R_out_opamp: float = 75.0,
) -> tuple[list[Component], dict[str, Node]]:
    """
    Inverting differentiator.

    ::

                  R_f
             ┌────┤────┐
             │         │
        n_in ── C_in ──┤(−)      │
                       │   U  ├──┘── n_out
                   n_gnd──(+)

    ``V_out(t) = −R_f · C · dV_in/dt``

    Parameters
    ----------
    prefix : str
        Name prefix.
    node_manager
        The circuit's NodeManager.
    n_in : Node
        Input node.
    n_out : Node
        Output node.
    n_gnd : Node
        Ground reference.
    c_in : float
        Input capacitor (F).
    r_f : float
        Feedback resistor (Ω).
    A_OL, R_in_opamp, R_out_opamp : float
        Op-amp model parameters.

    Returns
    -------
    (components, internal_nodes)
        *internal_nodes* keys: ``'inv_input'``.
    """
    n_inv = node_manager.AddNode(f"{prefix}_inv")

    comps: list[Component] = [
        Capacitor(f"{prefix}_Cin", (n_in, n_inv), capacitance=c_in),
        Resistor(f"{prefix}_Rf", (n_inv, n_out), resistance=r_f),
        OpAmp(f"{prefix}_U", (n_gnd, n_inv, n_out),
              A_OL=A_OL, R_in=R_in_opamp, R_out=R_out_opamp),
    ]
    return comps, {"inv_input": n_inv}
