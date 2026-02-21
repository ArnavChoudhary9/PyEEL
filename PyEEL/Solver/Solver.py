"""
Linear system solvers for MNA.

:class:`NumpySolver` uses LAPACK's ``dgesv`` (LU with **partial pivoting**),
which is the gold standard for dense direct solves and satisfies the
pivoting requirement for numerical stability.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import numpy as np

logger = logging.getLogger(__name__)


class LinearSolver(ABC):
    """
    Abstract interface for solving the linear system ``A x = b``.

    Subclass this to plug in different backends (dense, sparse, iterative,
    etc.).
    """

    @abstractmethod
    def Solve(self, matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
        """Solve ``matrix @ x = vector`` and return **x**."""
        ...


class NumpySolver(LinearSolver):
    """
    Direct dense solver using :func:`numpy.linalg.solve`.

    Internally calls LAPACK ``dgesv`` which performs **LU factorisation
    with partial pivoting** — the minimum requirement for a numerically
    stable direct solve.

    Parameters
    ----------
    check_condition : bool
        When ``True``, compute and log ``cond(A)`` on every call.
        Useful during development; disable in production for speed.
    condition_warning_threshold : float
        Emit a warning when ``cond(A)`` exceeds this value.
    """

    def __init__(
        self,
        check_condition: bool = False,
        condition_warning_threshold: float = 1e15,
    ):
        self._check_condition = check_condition
        self._condition_threshold = condition_warning_threshold
        self._last_condition_number: float | None = None

    @property
    def last_condition_number(self) -> float | None:
        """Condition number from the most recent solve (if monitoring is on)."""
        return self._last_condition_number

    def Solve(self, matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
        """
        Solve ``A x = b`` via LU with partial pivoting.

        Raises
        ------
        numpy.linalg.LinAlgError
            If the matrix is singular.
        RuntimeError
            If the solution contains NaN or Inf values.
        """
        # ── optional condition-number monitoring ────────────────────
        if self._check_condition:
            try:
                cond = float(np.linalg.cond(matrix))
                self._last_condition_number = cond
                if cond > self._condition_threshold:
                    logger.warning(
                        "Ill-conditioned matrix: cond(A) = %.2e "
                        "(threshold: %.2e). Results may be inaccurate.",
                        cond, self._condition_threshold,
                    )
            except np.linalg.LinAlgError:
                logger.warning("Could not compute condition number.")

        # ── solve (LAPACK dgesv — LU + partial pivoting) ───────────
        try:
            x = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError as exc:
            raise np.linalg.LinAlgError(
                "Singular matrix encountered during solve. "
                "Check circuit topology for floating nodes, "
                "capacitor-only cutsets, or inductor-only loops. "
                f"Original error: {exc}"
            ) from exc

        # ── sanity-check the result ─────────────────────────────────
        if not np.all(np.isfinite(x)):
            raise RuntimeError(
                "Solution contains NaN or Inf values. "
                "This typically indicates a singular or near-singular "
                "matrix. Check circuit topology and component values."
            )

        return x
