"""Op-amp circuit building blocks — amplifiers, integrators, differentiators."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...Core.Node import Node
from ..Passive.Resistor import Resistor
from ..Passive.Capacitor import Capacitor
from ..ICs.OpAmp import OpAmp

if TYPE_CHECKING:
    from ..Component import Component


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
    Inverting amplifier.  Gain ≈ ``-R_f / R_in``.

    Returns ``(components, {'inv_input'})``.
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
    Non-inverting amplifier.  Gain ≈ ``1 + R_f / R1``.

    Returns ``(components, {'inv_input'})``.
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
    Unity-gain voltage follower (buffer).  Gain = 1.

    Returns ``(components, {'feedback'})``.
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

    If all input resistors equal:
    ``V_out ≈ -(R_f / R_in) · (V_1 + V_2 + … + V_N)``

    Returns ``(components, {'summing_junction'})``.
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

    When ``R1 = R3`` and ``R2 = R_f``:
    ``V_out = (R_f / R1) · (V_pos - V_neg)``

    Returns ``(components, {'inv_input', 'noninv_input'})``.
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

    ``V_out(t) = -(1/RC) ∫ V_in dt``

    Returns ``(components, {'inv_input'})``.
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

    ``V_out(t) = -R_f · C · dV_in/dt``

    Returns ``(components, {'inv_input'})``.
    """
    n_inv = node_manager.AddNode(f"{prefix}_inv")

    comps: list[Component] = [
        Capacitor(f"{prefix}_Cin", (n_in, n_inv), capacitance=c_in),
        Resistor(f"{prefix}_Rf", (n_inv, n_out), resistance=r_f),
        OpAmp(f"{prefix}_U", (n_gnd, n_inv, n_out),
              A_OL=A_OL, R_in=R_in_opamp, R_out=R_out_opamp),
    ]
    return comps, {"inv_input": n_inv}
