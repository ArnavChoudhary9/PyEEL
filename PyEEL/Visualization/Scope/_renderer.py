"""
_renderer — pyqtgraph-based oscilloscope display.

Draws channel waveforms, graticule, trigger level indicator,
measurement HUD, and held waveforms.  Provides toolbar controls for
time-base, trigger, run/stop, auto-hold, and single-shot.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import numpy as np

from PyQt6 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

from ._measurements import compute_measurements, MeasurementResult, _fmt, _fmt_freq, _fmt_time

if TYPE_CHECKING:
    from ._channel import ScopeChannel
    from ._trigger import Trigger


# ── colours ─────────────────────────────────────────────────────────
_BG = "#1a1a2e"
_GRID = "#2a2a4a"
_TEXT = "#cccccc"
_TRIGGER_LINE_COLOUR = "#ff4444"


class ScopeRenderer(QtWidgets.QMainWindow):
    """
    The main oscilloscope window.

    This is intentionally a *dumb* renderer: it doesn't know about
    Circuit or Simulation — it only knows about :class:`ScopeChannel`
    objects and a :class:`Trigger`.
    """

    closed = QtCore.pyqtSignal()  # emitted when the window closes

    def __init__(
        self,
        channels: list[ScopeChannel],
        trigger: Trigger,
        *,
        title: str = "PyEEL Scope",
        window: float = 0.02,
        show_measurements: bool = True,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._channels = channels
        self._trigger = trigger
        self._time_window = window
        self._show_measurements = show_measurements
        self._running = True
        self._held_snapshots: list[list[tuple[np.ndarray, np.ndarray, str]]] = []
        self._auto_hold = False
        self._max_holds = 8

        self._init_ui(title)
        self._init_plot()
        self._init_toolbar()
        self._init_measurement_labels()

    # ================================================================
    # UI construction
    # ================================================================

    def _init_ui(self, title: str) -> None:
        self.setWindowTitle(title)
        self.resize(1100, 650)

        # dark palette
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#0f0f23"))
        palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(_TEXT))
        palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor("#16162b"))
        palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(_TEXT))
        palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor("#252545"))
        palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(_TEXT))
        self.setPalette(palette)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        self._layout = QtWidgets.QVBoxLayout(central)
        self._layout.setContentsMargins(4, 4, 4, 4)

    def _init_plot(self) -> None:
        pg.setConfigOptions(antialias=True)
        self._pw = pg.PlotWidget()
        self._pw.setBackground(_BG)
        self._pw.showGrid(x=True, y=True, alpha=0.25)
        self._pw.setLabel("bottom", "Time", units="s")
        self._pw.setLabel("left", "Amplitude")

        # ── trigger level line ──────────────────────────────────────
        self._trigger_line = pg.InfiniteLine(
            pos=self._trigger.level,
            angle=0,
            pen=pg.mkPen(_TRIGGER_LINE_COLOUR, width=1, style=QtCore.Qt.PenStyle.DashLine),
            movable=True,
            label="Trig",
            labelOpts={"color": _TRIGGER_LINE_COLOUR, "position": 0.05},
        )
        self._trigger_line.sigPositionChanged.connect(self._on_trigger_line_moved)
        self._pw.addItem(self._trigger_line)

        # ── channel curves ──────────────────────────────────────────
        for ch in self._channels:
            pen = pg.mkPen(ch.colour, width=1.5)
            curve = self._pw.plot([], [], pen=pen, name=ch.label)
            ch._curve_item = curve

        self._layout.addWidget(self._pw, stretch=1)

    def _init_toolbar(self) -> None:
        tb = QtWidgets.QHBoxLayout()

        # ── Run / Stop ──────────────────────────────────────────────
        self._btn_run = QtWidgets.QPushButton("Run")
        self._btn_run.setCheckable(True)
        self._btn_run.setChecked(True)
        self._btn_run.setStyleSheet(
            "QPushButton:checked { background: #226622; }"
            "QPushButton { background: #662222; padding: 4px 12px; }"
        )
        self._btn_run.toggled.connect(self._on_run_toggled)
        tb.addWidget(self._btn_run)

        # ── Single shot ─────────────────────────────────────────────
        btn_single = QtWidgets.QPushButton("Single")
        btn_single.setStyleSheet("padding: 4px 12px;")
        btn_single.clicked.connect(self._on_single)
        tb.addWidget(btn_single)

        # ── Auto Hold ───────────────────────────────────────────────
        self._btn_hold = QtWidgets.QPushButton("Auto Hold")
        self._btn_hold.setCheckable(True)
        self._btn_hold.setStyleSheet(
            "QPushButton:checked { background: #664400; }"
            "QPushButton { padding: 4px 12px; }"
        )
        self._btn_hold.toggled.connect(self._on_auto_hold_toggled)
        tb.addWidget(self._btn_hold)

        # ── Clear Holds ─────────────────────────────────────────────
        btn_clear = QtWidgets.QPushButton("Clear Holds")
        btn_clear.setStyleSheet("padding: 4px 12px;")
        btn_clear.clicked.connect(self._clear_holds)
        tb.addWidget(btn_clear)

        tb.addSpacing(20)

        # ── Time/div ────────────────────────────────────────────────
        tb.addWidget(QtWidgets.QLabel("Time/div:"))
        self._time_combo = QtWidgets.QComboBox()
        _tdivs = [
            ("1 µs",  1e-6),  ("2 µs",  2e-6),  ("5 µs",  5e-6),
            ("10 µs", 1e-5),  ("20 µs", 2e-5),  ("50 µs", 5e-5),
            ("100 µs", 1e-4), ("200 µs", 2e-4), ("500 µs", 5e-4),
            ("1 ms",  1e-3),  ("2 ms",  2e-3),  ("5 ms",  5e-3),
            ("10 ms", 1e-2),  ("20 ms", 2e-2),  ("50 ms", 5e-2),
            ("100 ms", 1e-1), ("200 ms", 2e-1), ("500 ms", 5e-1),
            ("1 s",   1.0),
        ]
        for label, val in _tdivs:
            self._time_combo.addItem(label, val)
        # default: pick closest to current window / 10
        target = self._time_window / 10
        best = min(range(len(_tdivs)), key=lambda i: abs(_tdivs[i][1] - target))
        self._time_combo.setCurrentIndex(best)
        self._time_combo.currentIndexChanged.connect(self._on_tdiv_changed)
        tb.addWidget(self._time_combo)

        tb.addSpacing(20)

        # ── Trigger controls ────────────────────────────────────────
        tb.addWidget(QtWidgets.QLabel("Trig:"))
        self._trig_mode_combo = QtWidgets.QComboBox()
        for m in ("Auto", "Normal", "Single", "Free"):
            self._trig_mode_combo.addItem(m)
        self._trig_mode_combo.currentTextChanged.connect(self._on_trig_mode)
        tb.addWidget(self._trig_mode_combo)

        self._trig_edge_combo = QtWidgets.QComboBox()
        for e in ("Rising", "Falling", "Either"):
            self._trig_edge_combo.addItem(e)
        self._trig_edge_combo.currentTextChanged.connect(self._on_trig_edge)
        tb.addWidget(self._trig_edge_combo)

        tb.addWidget(QtWidgets.QLabel("Level:"))
        self._trig_level_spin = QtWidgets.QDoubleSpinBox()
        self._trig_level_spin.setRange(-1e6, 1e6)
        self._trig_level_spin.setDecimals(4)
        self._trig_level_spin.setSingleStep(0.1)
        self._trig_level_spin.setValue(self._trigger.level)
        self._trig_level_spin.valueChanged.connect(self._on_trig_level)
        tb.addWidget(self._trig_level_spin)

        # ── Trigger source channel ──────────────────────────────────
        tb.addWidget(QtWidgets.QLabel("Src:"))
        self._trig_src_combo = QtWidgets.QComboBox()
        for ch in self._channels:
            self._trig_src_combo.addItem(f"CH{ch.index + 1}")
        self._trig_src_combo.currentIndexChanged.connect(self._on_trig_source)
        tb.addWidget(self._trig_src_combo)

        tb.addStretch()

        # ── Measurements toggle ─────────────────────────────────────
        self._btn_meas = QtWidgets.QPushButton("Meas")
        self._btn_meas.setCheckable(True)
        self._btn_meas.setChecked(self._show_measurements)
        self._btn_meas.setStyleSheet(
            "QPushButton:checked { background: #333366; }"
            "QPushButton { padding: 4px 12px; }"
        )
        self._btn_meas.toggled.connect(self._on_meas_toggled)
        tb.addWidget(self._btn_meas)

        self._layout.addLayout(tb)

    def _init_measurement_labels(self) -> None:
        """Create per-channel measurement text items on the plot."""
        self._meas_items: list[pg.TextItem] = []
        for i, ch in enumerate(self._channels):
            item = pg.TextItem(
                text="", color=ch.colour,
                anchor=(0, 0), fill=pg.mkBrush(0, 0, 0, 140)
            )
            item.setFont(QtGui.QFont("Consolas", 9))
            self._pw.addItem(item)
            item.setVisible(self._show_measurements)
            self._meas_items.append(item)

    # ================================================================
    # Rendering (called by Scope.Update)
    # ================================================================

    def draw_frame(self, dt: float) -> None:
        """
        Redraw all channel curves.  *dt* is the real-time elapsed
        since last render — used by the trigger engine.
        """
        if not self._running and not self._trigger.state.name == "TRIGGERED":
            return

        # latest time across all channels
        t_latest: float = 0.0
        for ch in self._channels:
            lt = ch.buffer.latest_time
            if lt is not None and lt > t_latest:
                t_latest = lt

        for ch in self._channels:
            if ch._curve_item is None:
                continue
            t, v = ch.get_display_data(window=self._time_window)
            if len(t) > 0:
                ch._curve_item.setData(t, v)

        # x-axis window
        if t_latest > 0:
            self._pw.setXRange(
                t_latest - self._time_window, t_latest
            )

        # auto-hold snapshot
        if self._auto_hold and self._running:
            self._capture_hold()

        # measurements HUD
        if self._show_measurements:
            self._update_measurements()

    def _update_measurements(self) -> None:
        vb = self._pw.getViewBox()
        view_range = vb.viewRange()
        y_range = view_range[1]
        x_range = view_range[0]

        for i, (ch, item) in enumerate(zip(self._channels, self._meas_items)):
            if not ch.visible or ch.buffer.size < 2:
                item.setText("")
                continue
            t, v = ch.get_display_data(window=self._time_window)
            if len(t) < 2:
                item.setText("")
                continue
            m = compute_measurements(t, v)
            item.setText(f"CH{ch.index + 1}: {m.summary_text(ch.unit)}")
            # stack measurements at top-left of view
            y_pos = y_range[1] - (i + 1) * (y_range[1] - y_range[0]) * 0.05
            item.setPos(x_range[0], y_pos)

    # ================================================================
    # Auto-hold
    # ================================================================

    def _capture_hold(self) -> None:
        snapshot: list[tuple[np.ndarray, np.ndarray, str]] = []
        for ch in self._channels:
            if not ch.visible:
                continue
            t, v = ch.get_display_data(window=self._time_window)
            if len(t) == 0:
                continue
            snapshot.append((t.copy(), v.copy(), ch.colour))

        if not snapshot:
            return

        self._held_snapshots.append(snapshot)

        # draw held curves (faint)
        for t, v, colour in snapshot:
            pen = pg.mkPen(colour, width=1, style=QtCore.Qt.PenStyle.DotLine)
            pen.setColor(QtGui.QColor(colour))
            c = self._pw.plot(t, v, pen=pen)
            c.setZValue(-10)
            # store reference so we can remove later
            for ch in self._channels:
                if ch.colour == colour:
                    ch._hold_curves.append(c)
                    break

        # limit hold count
        while len(self._held_snapshots) > self._max_holds:
            self._held_snapshots.pop(0)
            for ch in self._channels:
                if ch._hold_curves:
                    old = ch._hold_curves.pop(0)
                    self._pw.removeItem(old)

    def _clear_holds(self) -> None:
        for ch in self._channels:
            for curve in ch._hold_curves:
                self._pw.removeItem(curve)
            ch._hold_curves.clear()
        self._held_snapshots.clear()

    # ================================================================
    # Toolbar callbacks
    # ================================================================

    def _on_run_toggled(self, checked: bool) -> None:
        self._running = checked
        self._btn_run.setText("Run" if checked else "Stop")

    def _on_single(self) -> None:
        from ._trigger import TriggerMode
        self._trigger.mode = TriggerMode.SINGLE
        self._trigger.arm()
        self._running = True
        self._btn_run.setChecked(True)
        self._trig_mode_combo.blockSignals(True)
        self._trig_mode_combo.setCurrentText("Single")
        self._trig_mode_combo.blockSignals(False)

    def _on_auto_hold_toggled(self, checked: bool) -> None:
        self._auto_hold = checked

    def _on_tdiv_changed(self, idx: int) -> None:
        val = self._time_combo.itemData(idx)
        if val is not None:
            self._time_window = val * 10  # 10 divisions

    def _on_trig_mode(self, text: str) -> None:
        from ._trigger import TriggerMode
        mapping = {
            "Auto": TriggerMode.AUTO,
            "Normal": TriggerMode.NORMAL,
            "Single": TriggerMode.SINGLE,
            "Free": TriggerMode.FREE,
        }
        mode = mapping.get(text)
        if mode is not None:
            self._trigger.mode = mode

    def _on_trig_edge(self, text: str) -> None:
        from ._trigger import TriggerEdge
        mapping = {
            "Rising": TriggerEdge.RISING,
            "Falling": TriggerEdge.FALLING,
            "Either": TriggerEdge.EITHER,
        }
        edge = mapping.get(text)
        if edge is not None:
            self._trigger.edge = edge

    def _on_trig_level(self, value: float) -> None:
        self._trigger.level = value
        self._trigger_line.blockSignals(True)
        self._trigger_line.setValue(value)
        self._trigger_line.blockSignals(False)

    def _on_trig_source(self, idx: int) -> None:
        if 0 <= idx < len(self._channels):
            self._trigger.source = self._channels[idx]

    def _on_trigger_line_moved(self) -> None:
        val: float = float(self._trigger_line.value())  # type: ignore[arg-type]
        self._trigger.level = val
        self._trig_level_spin.blockSignals(True)
        self._trig_level_spin.setValue(val)
        self._trig_level_spin.blockSignals(False)

    def _on_meas_toggled(self, checked: bool) -> None:
        self._show_measurements = checked
        for item in self._meas_items:
            item.setVisible(checked)

    # ================================================================
    # Window lifecycle
    # ================================================================

    @property
    def is_open(self) -> bool:
        return self.isVisible()

    def closeEvent(self, a0: QtGui.QCloseEvent | None) -> None:  # type: ignore[override]
        self.closed.emit()
        super().closeEvent(a0)
