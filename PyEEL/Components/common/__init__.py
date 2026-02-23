"""
Common circuit building blocks — factory helpers.

Split into category sub-modules for maintainability.
All public names are re-exported here so that existing imports
(``from PyEEL.Components.common import voltage_divider``) still work.
"""

from .passive_networks import (
    voltage_divider,
    rc_low_pass,
    rc_high_pass,
    series_lcr,
    parallel_rc,
)
from .diode_circuits import (
    half_wave_rectifier,
    full_bridge_rectifier,
    zener_clamp,
    zener_regulator,
)
from .amplifier_circuits import (
    ce_amplifier,
    ce_amplifier_with_nodes,
    common_source_amplifier,
)
from .power_supply import (
    dc_supply,
    ac_supply,
    linear_power_supply,
    transformer_supply,
)
from .opamp_circuits import (
    inverting_amplifier,
    non_inverting_amplifier,
    voltage_follower,
    summing_amplifier,
    difference_amplifier,
    integrator,
    differentiator,
)
from .comparator_circuits import (
    voltage_comparator,
    schmitt_trigger,
    window_comparator,
)
from .utils import add_all

__all__ = [
    # Passive networks
    "voltage_divider", "rc_low_pass", "rc_high_pass",
    "series_lcr", "parallel_rc",
    # Diode circuits
    "half_wave_rectifier", "full_bridge_rectifier",
    "zener_clamp", "zener_regulator",
    # Amplifier stages
    "ce_amplifier", "ce_amplifier_with_nodes",
    "common_source_amplifier",
    # Power supplies
    "dc_supply", "ac_supply",
    "linear_power_supply", "transformer_supply",
    # Op-amp circuits
    "inverting_amplifier", "non_inverting_amplifier",
    "voltage_follower", "summing_amplifier",
    "difference_amplifier", "integrator", "differentiator",
    # Comparator circuits
    "voltage_comparator", "schmitt_trigger", "window_comparator",
    # Utilities
    "add_all",
]
