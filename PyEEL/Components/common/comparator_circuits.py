"""Comparator circuit building blocks — basic comparator, Schmitt trigger, window."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...Core.Node import Node
from ..Passive.Resistor import Resistor
from ..ICs.Comparator import Comparator

if TYPE_CHECKING:
    from ..Component import Component


def voltage_comparator(
    prefix: str,
    n_in: Node,
    n_ref: Node,
    n_out: Node,
    *,
    V_high: float = 5.0,
    V_low: float = 0.0,
    R_in: float = 1e6,
    R_out: float = 50.0,
) -> list[Component]:
    """
    Basic voltage comparator.

    * ``V_out = V_high`` when ``V_in > V_ref``
    * ``V_out = V_low``  when ``V_in < V_ref``

    Returns ``[C]``.
    """
    return [
        Comparator(f"{prefix}_C", (n_in, n_ref, n_out),
                   V_high=V_high, V_low=V_low,
                   R_in=R_in, R_out=R_out),
    ]


def schmitt_trigger(
    prefix: str,
    node_manager,
    n_in: Node,
    n_out: Node,
    n_ref: Node,
    *,
    r_upper: float = 100e3,
    r_lower: float = 10e3,
    V_supply: float = 5.0,
    V_hys: float | None = None,
    R_in: float = 1e6,
    R_out: float = 50.0,
) -> tuple[list[Component], dict[str, Node]]:
    """
    Non-inverting Schmitt trigger with hysteresis.

    Returns ``(components, {'noninv_input'})``.
    """
    n_ni = node_manager.AddNode(f"{prefix}_ni")
    hys_kw: dict[str, float] = {} if V_hys is None else {"V_hys": V_hys}
    comps: list[Component] = [  # type: ignore[assignment]
        Resistor(f"{prefix}_Rupper", (n_out, n_ni), resistance=r_upper),
        Resistor(f"{prefix}_Rlower", (n_ni, n_ref), resistance=r_lower),
        Comparator(f"{prefix}_C", (n_ni, n_ref, n_out),
                   V_high=V_supply, V_low=0.0,
                   R_in=R_in, R_out=R_out, **hys_kw),  # type: ignore[arg-type]
    ]
    return comps, {"noninv_input": n_ni}


def window_comparator(
    prefix: str,
    n_in: Node,
    n_out_high: Node,
    n_out_low: Node,
    n_ref_high: Node,
    n_ref_low: Node,
    *,
    V_high: float = 5.0,
    V_low: float = 0.0,
    R_in: float = 1e6,
    R_out: float = 50.0,
) -> tuple[list[Component], dict]:
    """
    Window comparator — two comparators detect if a signal is inside
    a voltage window ``[V_ref_low, V_ref_high]``.

    * ``n_out_high`` HIGH when ``V_in > V_ref_high``
    * ``n_out_low``  HIGH when ``V_in < V_ref_low``
    * Both LOW when signal is inside the window.

    Returns ``(components, {})``.
    """
    return [
        Comparator(f"{prefix}_C_high", (n_in, n_ref_high, n_out_high),
                   V_high=V_high, V_low=V_low, R_in=R_in, R_out=R_out),
        Comparator(f"{prefix}_C_low",  (n_ref_low, n_in, n_out_low),
                   V_high=V_high, V_low=V_low, R_in=R_in, R_out=R_out),
    ], {}
