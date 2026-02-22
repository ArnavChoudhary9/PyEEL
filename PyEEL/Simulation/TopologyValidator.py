"""
Topology validator — checks a circuit for common structural problems.

Extracted from ``Circuit._validate_topology`` to honour the
single-responsibility principle.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..Core.NodeManager import NodeManager
    from ..Components.Component import Component

logger = logging.getLogger(__name__)


class TopologyValidator:
    """
    Static-analysis checks for circuit topology.

    All checks emit warnings (they do not raise) so the simulation
    can still attempt to run — Gmin may save a marginal topology.
    """

    @staticmethod
    def validate(components: list[Component],
                 node_manager: NodeManager) -> None:
        """Run every topology check."""
        TopologyValidator._check_isolated_nodes(components, node_manager)
        TopologyValidator._check_capacitor_only_nodes(components, node_manager)
        TopologyValidator._check_voltage_source_loops(components)
        TopologyValidator._check_extreme_values(components)

    # ── individual checks ───────────────────────────────────────────

    @staticmethod
    def _check_isolated_nodes(components: list[Component],
                              node_manager: NodeManager) -> None:
        """Warn about nodes that aren't connected to any component."""
        nv = node_manager.VoltageUnknownCount
        node_comps: dict[int, list[Component]] = {i: [] for i in range(nv)}

        for comp in components:
            for node in comp.Nodes:
                if node.Index is not None and node.Index < nv:
                    node_comps[node.Index].append(comp)

        for idx, comps in node_comps.items():
            if not comps:
                name = TopologyValidator._find_node_name(idx, node_manager)
                logger.warning(
                    "Node '%s' (index %d) is not connected to any component. "
                    "This will cause a singular matrix.",
                    name, idx,
                )

    @staticmethod
    def _check_capacitor_only_nodes(components: list[Component],
                                    node_manager: NodeManager) -> None:
        """Warn about nodes connected only through capacitors (DC-floating)."""
        from ..Components.Passive.Capacitor import Capacitor

        nv = node_manager.VoltageUnknownCount
        node_comps: dict[int, list[Component]] = {i: [] for i in range(nv)}

        for comp in components:
            for node in comp.Nodes:
                if node.Index is not None and node.Index < nv:
                    node_comps[node.Index].append(comp)

        for idx, comps in node_comps.items():
            if comps and all(isinstance(c, Capacitor) for c in comps):
                name = TopologyValidator._find_node_name(idx, node_manager)
                logger.warning(
                    "Node '%s' is only connected through capacitors "
                    "(DC-floating). Gmin will stabilise it, but this "
                    "may indicate a topology error.",
                    name,
                )

    @staticmethod
    def _check_voltage_source_loops(components: list[Component]) -> None:
        """Warn about contradictory KVL constraints from parallel voltage sources."""
        from ..Components.Sources.VoltageSource import VoltageSource

        vs_pairs: dict[tuple[int | None, int | None], list[str]] = {}
        for comp in components:
            if isinstance(comp, VoltageSource):
                n1_idx = comp.Nodes[0].Index
                n2_idx = comp.Nodes[1].Index
                key = (min(n1_idx or -1, n2_idx or -1),
                       max(n1_idx or -1, n2_idx or -1))
                vs_pairs.setdefault(key, []).append(comp.Name)
        for key, names in vs_pairs.items():
            if len(names) > 1:
                logger.warning(
                    "Voltage sources %s share the same node pair — "
                    "this creates conflicting KVL constraints and "
                    "will likely produce a singular matrix.",
                    names,
                )

    @staticmethod
    def _check_extreme_values(components: list[Component]) -> None:
        """Warn about component values that may cause ill-conditioning."""
        from ..Components.Passive.Resistor import Resistor
        from ..Components.Passive.Capacitor import Capacitor
        from ..Components.Passive.Inductor import Inductor

        for comp in components:
            if isinstance(comp, Resistor):
                if comp.Resistance > 1e15 or comp.Resistance < 1e-15:
                    logger.warning(
                        "Resistor '%s' has extreme value %.2e Ω — "
                        "consider rescaling for better conditioning.",
                        comp.Name, comp.Resistance,
                    )
            elif isinstance(comp, Capacitor):
                if comp.Capacitance > 1e6 or comp.Capacitance < 1e-18:
                    logger.warning(
                        "Capacitor '%s' has extreme value %.2e F — "
                        "consider rescaling for better conditioning.",
                        comp.Name, comp.Capacitance,
                    )
            elif isinstance(comp, Inductor):
                if comp.Inductance > 1e6 or comp.Inductance < 1e-18:
                    logger.warning(
                        "Inductor '%s' has extreme value %.2e H — "
                        "consider rescaling for better conditioning.",
                        comp.Name, comp.Inductance,
                    )

    # ── helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _find_node_name(index: int, node_manager: NodeManager) -> str:
        """Return the human-readable name of the node at *index*."""
        for name, node in node_manager._Nodes.items():
            if node.Index == index:
                return name
        return f"<index {index}>"
