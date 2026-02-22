"""
Energy checker — verifies reactive component energies stay physical.

Extracted from ``Circuit._check_energy`` to honour SRP.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ..Components.Component import Component

logger = logging.getLogger(__name__)


class EnergyChecker:
    """
    Checks that energy stored in reactive components has not exploded
    to non-physical levels.  Emits warnings rather than raising.
    """

    @staticmethod
    def check(components: list[Component],
              solution: np.ndarray,
              max_energy: float) -> None:
        """
        Iterate over reactive components and warn if energy exceeds
        *max_energy* joules.
        """
        from ..Components.Passive.Capacitor import Capacitor
        from ..Components.Passive.Inductor import Inductor

        for comp in components:
            if isinstance(comp, Capacitor):
                v = comp.GetVoltage(solution)
                energy = 0.5 * comp.Capacitance * v * v
                if energy > max_energy:
                    logger.warning(
                        "Capacitor '%s': energy = %.2e J exceeds "
                        "threshold %.2e J — possible instability.",
                        comp.Name, energy, max_energy,
                    )
            elif isinstance(comp, Inductor):
                i = comp._current
                energy = 0.5 * comp.Inductance * i * i
                if energy > max_energy:
                    logger.warning(
                        "Inductor '%s': energy = %.2e J exceeds "
                        "threshold %.2e J — possible instability.",
                        comp.Name, energy, max_energy,
                    )
