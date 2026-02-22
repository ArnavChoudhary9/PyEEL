"""
Backward-compatibility shim.

Import from ``PyEEL.Solver.LinearSolver`` instead.
"""

from .LinearSolver import LinearSolver, NumpySolver

__all__ = ["LinearSolver", "NumpySolver"]
