"""
PyEEL — Zener Diode Voltage Regulator
=======================================
Demonstrates a classic Zener-diode shunt regulator powered from a
half-wave rectified and filtered AC supply.

Topology::

    V1 (AC 12 V peak, 50 Hz)
     │
    (n_ac)
     │
    D1  ← half-wave rectifier diode (anode → cathode)
     │
    (n_rect) ─── C_filter (470 µF) ─── GND
     │
    R_series (470 Ω)
     │
    (n_out) ──┬── R_load (2 kΩ) ─── GND
              │
             DZ1  ← Zener 5.1 V
              │     (anode=GND, cathode=n_out)
             GND

How it works
------------
The AC source is half-wave rectified by D1.  C_filter smooths the
pulsing DC to an unregulated ~11.3 V rail (n_rect) with some
residual ripple at 50 Hz.  R_series drops the excess voltage, and the
5.1 V Zener clamps n_out to the Zener voltage regardless of supply
ripple or load variation.

Expected operating point
------------------------
  V(n_rect) ≈ 11.3 V (peak - V_f, with ripple)
  V(n_out)  ≈  5.1 V (regulated)
  I_series  ≈ (11.3 - 5.1) / 470 Ω  ≈  13 mA

Probes
------
  • V(n_rect) — unregulated, rippled DC rail
  • V(n_out)  — Zener-regulated output
  • I(DZ1)    — Zener current (shows how regulation absorbs ripple)
"""

from PyEEL import *

# ── simulation config ────────────────────────────────────────────────
config = SimulationConfig(
    dc_operating_point=True,
    gmin=1e-12,
)

# ── build circuit ────────────────────────────────────────────────────
ckt = Circuit(solver=NumpySolver(), config=config)

nm    = ckt.NodeManager
gnd   = nm.GroundNode
n_ac  = nm.AddNode("n_ac")     # AC source output
n_rect = nm.AddNode("n_rect")  # after rectifier diode / filter cap
n_out  = nm.AddNode("n_out")   # regulated output node

# ── AC source ───────────────────────────────────────────────────────
ckt.AddComponent(ACVoltageSource("V1", (n_ac, gnd),
                                  amplitude=12.0, frequency=50.0))

# ── half-wave rectifier ─────────────────────────────────────────────
ckt.AddComponent(d1 := Diode("D1", (n_ac, n_rect)))

# ── filter capacitor ────────────────────────────────────────────────
ckt.AddComponent(Capacitor("C_filter", (n_rect, gnd), capacitance=470e-6))

# ── series resistor (current limiter for Zener) ─────────────────────
ckt.AddComponent(Resistor("R_series", (n_rect, n_out), resistance=470.0))

# ── Zener diode (cathode = n_out, anode = GND — reverse biased) ─────
ckt.AddComponent(dz1 := ZenerDiode("DZ1", (gnd, n_out), Vz=5.1,
                                    Ibv=5e-3, n_bv=0.5))

# ── load resistor ───────────────────────────────────────────────────
ckt.AddComponent(Resistor("R_load", (n_out, gnd), resistance=2000.0))

# ── probes ───────────────────────────────────────────────────────────
v_rect = VoltageProbe("V(unregulated)", n_rect)   # unregulated rail
v_out  = VoltageProbe("V(regulated)",  n_out)     # regulated output
i_dz1  = CurrentProbe("I(DZ1)",        dz1)       # Zener current

ckt.AddProbe(v_rect)
ckt.AddProbe(v_out)
ckt.AddProbe(i_dz1)

# ── live simulation ──────────────────────────────────────────────────
ckt.Finalize()

scope = Scope(
    [v_rect, v_out],
    [i_dz1],
    window=100e-3,
    title="Zener Voltage Regulator",
)

sim = LiveSimulation(
    ckt, scope,
    dt=2e-4,
    speed=50,
)

sim.Run()
