"""Deprecated shim — import from ``PyEEL.Solver.LinearSolver`` directly instead."""
import warnings as _w
_w.warn(
    "Importing from 'PyEEL.Solver.Solver' is deprecated. Use 'from PyEEL.Solver import LinearSolver' instead.",
    DeprecationWarning, stacklevel=2,
)
from .LinearSolver import LinearSolver, NumpySolver  # noqa: F401, E402
__all__ = ["LinearSolver", "NumpySolver"]
