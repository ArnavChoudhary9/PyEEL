"""
PyEEL – main test / demo script
================================
Runs three test circuits to verify MNA stamping, the probe system, and
AC transient simulation.
"""

from PyEEL import *
from PyEEL.Circuit import Circuit
from PyEEL.Solver.Solver import NumpySolver
from PyEEL.Components.Sources.VoltageSource import (
    VoltageSource, DCVoltageSource, ACVoltageSource,
)
from PyEEL.Probe import VoltageProbe, CurrentProbe

import math

# ─── helpers ────────────────────────────────────────────────────────
PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

def assert_close(actual: float, expected: float, label: str,
                 tol: float = 1e-9) -> bool:
    ok = abs(actual - expected) < tol
    tag = PASS if ok else FAIL
    print(f"  [{tag}] {label}: got {actual:.6g}, expected {expected:.6g}")
    return ok


# ═══════════════════════════════════════════════════════════════════
#  TEST 1 – Simple DC circuit  (5 V source + 1 kΩ resistor to GND)
# ═══════════════════════════════════════════════════════════════════
def test_dc_simple():
    print("\n=== Test 1: DC source + single resistor ===")

    ckt = Circuit(NumpySolver())
    gnd = ckt.NodeManager.GroundNode
    n1  = ckt.NodeManager.AddNode("N1")          # index 0

    vs = DCVoltageSource("VS", (n1, gnd), 5.0)
    r1 = Resister("R1", (n1, gnd), 1000.0)

    ckt.AddComponent(vs)
    ckt.AddComponent(r1)

    # Probes
    vp = VoltageProbe("V_N1", n1)
    ip = CurrentProbe("I_R1", r1)
    ckt.AddProbe(vp)
    ckt.AddProbe(ip)

    ckt.Finalize()
    sol = ckt.Simulate(1e-3)

    ok  = assert_close(vp.ValueData[0], 5.0,   "V(N1)")
    ok &= assert_close(ip.ValueData[0], 5e-3,  "I(R1) = 5 V / 1 kΩ")
    return ok


# ═══════════════════════════════════════════════════════════════════
#  TEST 2 – Voltage divider  (5 V → R1 → N2 → R2 → GND)
# ═══════════════════════════════════════════════════════════════════
def test_voltage_divider():
    print("\n=== Test 2: Voltage divider ===")

    ckt = Circuit(NumpySolver())
    gnd = ckt.NodeManager.GroundNode
    n1  = ckt.NodeManager.AddNode("N1")
    n2  = ckt.NodeManager.AddNode("N2")

    vs = DCVoltageSource("VS", (n1, gnd), 5.0)
    r1 = Resister("R1", (n1, n2), 1000.0)
    r2 = Resister("R2", (n2, gnd), 1000.0)

    ckt.AddComponent(vs)
    ckt.AddComponent(r1)
    ckt.AddComponent(r2)

    # Probes
    v_n1   = VoltageProbe("V_N1", n1)
    v_n2   = VoltageProbe("V_N2", n2)
    v_diff = VoltageProbe("V_R1", n1, n2)
    i_r1   = CurrentProbe("I_R1", r1)
    i_vs   = CurrentProbe("I_VS", vs)

    for p in (v_n1, v_n2, v_diff, i_r1, i_vs):
        ckt.AddProbe(p)

    ckt.Finalize()
    ckt.Simulate(1e-3)

    ok  = assert_close(v_n1.ValueData[0],  5.0,    "V(N1)")
    ok &= assert_close(v_n2.ValueData[0],  2.5,    "V(N2) = 5 V × R2/(R1+R2)")
    ok &= assert_close(v_diff.ValueData[0], 2.5,   "V(N1)-V(N2)")
    ok &= assert_close(i_r1.ValueData[0],  2.5e-3, "I(R1)")
    ok &= assert_close(i_vs.ValueData[0], -2.5e-3, "I(VS) (negative = delivering)")

    # ── demo: print probe ──
    v_n2.Print()
    return ok


# ═══════════════════════════════════════════════════════════════════
#  TEST 3 – AC transient  (sine source into resistive divider)
# ═══════════════════════════════════════════════════════════════════
def test_ac_transient():
    print("\n=== Test 3: AC transient ===")

    freq      = 50.0          # 50 Hz
    amplitude = 10.0          # 10 V peak
    periods   = 2             # simulate 2 full periods
    steps_per_period = 200
    dt        = 1.0 / (freq * steps_per_period)
    total     = int(periods * steps_per_period)

    ckt = Circuit(NumpySolver())
    gnd = ckt.NodeManager.GroundNode
    n1  = ckt.NodeManager.AddNode("N1")
    n2  = ckt.NodeManager.AddNode("N2")

    vs = ACVoltageSource("VS_AC", (n1, gnd), amplitude, freq)
    r1 = Resister("R1", (n1, n2), 1000.0)
    r2 = Resister("R2", (n2, gnd), 1000.0)

    ckt.AddComponent(vs)
    ckt.AddComponent(r1)
    ckt.AddComponent(r2)

    v_n2 = VoltageProbe("V_N2_AC", n2)
    i_r2 = CurrentProbe("I_R2", r2)
    ckt.AddProbe(v_n2)
    ckt.AddProbe(i_r2)

    ckt.Finalize()

    for _ in range(total):
        ckt.Simulate(dt)

    # At t ≈ T/4 the sine peaks → V(N2) ≈ amplitude/2
    ok = True

    # Check that the peak of V(N2) is roughly amplitude/2
    v_peak = max(v_n2.ValueData)
    ok &= assert_close(v_peak, amplitude / 2, "V(N2) peak ≈ A/2", tol=0.05)

    # Check last value against the analytic sine at that time.
    # Note: The probe records at time t_record = t_before + dt, but the
    # waveform was evaluated at t_before (context.Time).  So the actual
    # value corresponds to the waveform at (t_record - dt).
    t_last = v_n2.TimeData[-1]
    t_eval = t_last - dt
    expected_v = (amplitude / 2) * math.sin(2 * math.pi * freq * t_eval)
    ok &= assert_close(v_n2.ValueData[-1], expected_v,
                        "V(N2) last sample", tol=1e-9)

    # ── demo: save to CSV ──
    v_n2.Save("v_n2_ac_probe.csv")

    # ── demo: plot (uncomment below to display) ──
    # v_n2.Plot()                      # full history
    # v_n2.Plot(window=1.0 / freq)     # last period only

    return ok


# ═══════════════════════════════════════════════════════════════════
#  Run all tests
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    results = [
        test_dc_simple(),
        test_voltage_divider(),
        test_ac_transient(),
    ]

    print("\n" + "=" * 50)
    passed = sum(results)
    total  = len(results)
    print(f"Results: {passed}/{total} tests passed.")
    if all(results):
        print("All tests passed!")
    else:
        print("Some tests failed.")
