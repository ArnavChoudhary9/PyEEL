from enum import Enum, auto
from .Node import Node
from .Components.Component import Component

import numpy as np


class ProbeType(Enum):
    VOLTAGE = auto()
    CURRENT = auto()


class Probe:
    """
    A measurement probe that records simulation data at circuit nodes.
    
    Accepts nodes as arguments:
      - 1 node  → measures voltage at that node (relative to ground)
      - 2 nodes → measures voltage difference (V_n1 - V_n2)
    
    For current measurement, a component reference is required.
    
    Output modes:
      - Print()  → prints recorded data to the console
      - Save()   → saves recorded data to a CSV file
      - Plot()   → plots data with an optional time window to maintain detail
    """

    _Name: str
    _Type: ProbeType
    _Nodes: tuple[Node, ...]
    _Component: Component | None

    _TimeData: list[float]
    _ValueData: list[float]

    def __init__(self, name: str, probe_type: ProbeType, *nodes: Node,
                 component: Component | None = None):
        self._Name = name
        self._Type = probe_type
        self._Nodes = nodes
        self._Component = component
        self._TimeData = []
        self._ValueData = []

        # ── validation ──────────────────────────────────────────────
        if probe_type == ProbeType.VOLTAGE:
            if len(nodes) < 1 or len(nodes) > 2:
                raise ValueError(
                    f"Probe '{name}': Voltage probe requires 1 or 2 nodes, "
                    f"got {len(nodes)}."
                )
        elif probe_type == ProbeType.CURRENT:
            if component is None:
                raise ValueError(
                    f"Probe '{name}': Current probe requires a component reference."
                )

    # ── properties ──────────────────────────────────────────────────
    @property
    def Name(self) -> str: return self._Name
    @property
    def Type(self) -> ProbeType: return self._Type
    @property
    def Nodes(self) -> tuple[Node, ...]: return self._Nodes
    @property
    def Component(self) -> Component | None: return self._Component
    @property
    def TimeData(self) -> list[float]: return self._TimeData
    @property
    def ValueData(self) -> list[float]: return self._ValueData

    # ── data extraction ─────────────────────────────────────────────
    def _Extract(self, solution: np.ndarray) -> float:
        if self._Type == ProbeType.VOLTAGE:
            if len(self._Nodes) == 1:
                node = self._Nodes[0]
                return float(solution[node.Index]) if node.Index is not None else 0.0
            else:
                n1, n2 = self._Nodes[0], self._Nodes[1]
                v1 = float(solution[n1.Index]) if n1.Index is not None else 0.0
                v2 = float(solution[n2.Index]) if n2.Index is not None else 0.0
                return v1 - v2

        elif self._Type == ProbeType.CURRENT:
            return self._Component.GetCurrent(solution)  # type: ignore[union-attr]

        return 0.0

    # ── recording ───────────────────────────────────────────────────
    def Record(self, time: float, solution: np.ndarray) -> None:
        """Record one data-point. Called automatically by Circuit.Simulate()."""
        value = self._Extract(solution)
        self._TimeData.append(time)
        self._ValueData.append(value)

    def Clear(self) -> None:
        """Discard all recorded data."""
        self._TimeData.clear()
        self._ValueData.clear()

    # ── output: print ───────────────────────────────────────────────
    def Print(self) -> None:
        """Print all recorded data to the console."""
        unit = "V" if self._Type == ProbeType.VOLTAGE else "A"
        label = self._get_label()
        print(f"--- Probe: {self._Name} ({label}) ---")
        for t, v in zip(self._TimeData, self._ValueData):
            print(f"  t = {t:.6e} s  |  {v:+.6e} {unit}")
        print(f"--- End of Probe: {self._Name} ---\n")

    # ── output: save to file ────────────────────────────────────────
    def Save(self, file_path: str | None = None) -> None:
        """Save recorded data to a CSV file."""
        path = file_path or f"{self._Name}_probe.csv"
        unit = "V" if self._Type == ProbeType.VOLTAGE else "A"
        with open(path, "w") as f:
            f.write(f"Time (s),{self._get_label()} ({unit})\n")
            for t, v in zip(self._TimeData, self._ValueData):
                f.write(f"{t},{v}\n")
        print(f"Probe '{self._Name}' data saved to '{path}'.")

    # ── output: plot ────────────────────────────────────────────────
    def Plot(self, window: float | None = None) -> None:
        """
        Plot recorded data.

        Parameters
        ----------
        window : float | None
            If given, only the last *window* seconds of data are shown.
            This prevents the x-axis from growing indefinitely and keeps
            the waveform detail visible.
        """
        import matplotlib.pyplot as plt

        if not self._TimeData:
            print(f"Probe '{self._Name}' has no data to plot.")
            return

        t = np.array(self._TimeData)
        v = np.array(self._ValueData)

        # Apply time-window clipping
        if window is not None and len(t) > 0:
            t_max = t[-1]
            mask = t >= (t_max - window)
            t = t[mask]
            v = v[mask]

        unit = "V" if self._Type == ProbeType.VOLTAGE else "A"
        label = self._get_label()

        fig, ax = plt.subplots()
        ax.plot(t, v, linewidth=1.0)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel(f"{label} ({unit})")
        ax.set_title(f"Probe: {self._Name}")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        plt.show()

    # ── helpers ─────────────────────────────────────────────────────
    def _get_label(self) -> str:
        if self._Type == ProbeType.VOLTAGE:
            if len(self._Nodes) == 1:
                return f"V({self._Nodes[0].Name})"
            else:
                return f"V({self._Nodes[0].Name}) - V({self._Nodes[1].Name})"
        elif self._Type == ProbeType.CURRENT:
            if self._Component:
                return f"I({self._Component.Name})"
            return f"I({self._Nodes[0].Name} -> {self._Nodes[1].Name})"
        return "Unknown"

    def __str__(self) -> str:
        return f"Probe({self._Name}, {self._get_label()})"

    def __repr__(self) -> str:
        return self.__str__()


# ── convenience factory functions ───────────────────────────────────
def VoltageProbe(name: str, *nodes: Node) -> Probe:
    """Create a voltage probe. 1 node → absolute voltage, 2 nodes → V_diff."""
    return Probe(name, ProbeType.VOLTAGE, *nodes)


def CurrentProbe(name: str, component: Component) -> Probe:
    """Create a current probe that measures current through a component."""
    return Probe(name, ProbeType.CURRENT, *component.Nodes, component=component)
