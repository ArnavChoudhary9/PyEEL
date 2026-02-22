"""
Shared MNA stamping utility functions.

These helpers implement the common matrix stamp patterns used by
multiple components, reducing code duplication and ensuring
consistent MNA assembly.

All functions accept ``int | None`` for node indices — ``None``
means the node is ground and the corresponding row/column is
simply skipped.
"""

from __future__ import annotations

import numpy as np


def stamp_conductance(A: np.ndarray,
                      na: int | None, nb: int | None,
                      G: float) -> None:
    """
    Stamp conductance *G* between node indices *na* and *nb*.

    Equivalent to a resistor with ``G = 1/R`` connected between the
    two nodes::

        A[na, na] += G    A[na, nb] -= G
        A[nb, na] -= G    A[nb, nb] += G
    """
    if na is not None and nb is not None:
        A[na, na] += G;  A[na, nb] -= G
        A[nb, na] -= G;  A[nb, nb] += G
    elif na is not None:
        A[na, na] += G
    elif nb is not None:
        A[nb, nb] += G


def stamp_transconductance(A: np.ndarray,
                           n_out_p: int | None, n_out_n: int | None,
                           n_in_p: int | None, n_in_n: int | None,
                           Gm: float) -> None:
    """
    Stamp a voltage-controlled current source (transconductance).

    Current ``Gm · (V(n_in_p) - V(n_in_n))`` flows from *n_out_p*
    toward *n_out_n*.
    """
    if n_out_p is not None:
        if n_in_p is not None:
            A[n_out_p, n_in_p] += Gm
        if n_in_n is not None:
            A[n_out_p, n_in_n] -= Gm
    if n_out_n is not None:
        if n_in_p is not None:
            A[n_out_n, n_in_p] -= Gm
        if n_in_n is not None:
            A[n_out_n, n_in_n] += Gm


def stamp_current_source(b: np.ndarray,
                         n_from: int | None, n_to: int | None,
                         I: float) -> None:
    """
    Stamp a current source *I* flowing from *n_from* to *n_to*.

    In the MNA convention (current *leaving* a node is positive in b),
    the source *subtracts* from ``b[n_from]`` and *adds* to ``b[n_to]``.
    """
    if n_from is not None:
        b[n_from] -= I
    if n_to is not None:
        b[n_to] += I


def get_voltage_across(solution: np.ndarray,
                       n_pos: int | None, n_neg: int | None) -> float:
    """Return ``V(n_pos) - V(n_neg)`` from a solution vector."""
    v1 = float(solution[n_pos]) if n_pos is not None else 0.0
    v2 = float(solution[n_neg]) if n_neg is not None else 0.0
    return v1 - v2
