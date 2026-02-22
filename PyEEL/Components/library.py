"""
Pre-built component library — real-world parts with datasheet values.

Every function takes only a **name** and **nodes**, returns a ready-to-use
component instance.  No need to look up datasheet parameters.

Usage::

    from PyEEL.Components.library import R1k, IN4007, BC547

    ckt.AddComponent(R1k("R1", (n1, n2)))
    ckt.AddComponent(IN4007("D1", (n_a, n_k)))
    ckt.AddComponent(BC547("Q1", (n_c, n_b, n_e)))
"""

from __future__ import annotations

from ..Core.Node import Node
from .Passive.Resistor import Resistor
from .Passive.Capacitor import Capacitor
from .Passive.Inductor import Inductor
from .Semiconductors.Diode import Diode
from .Semiconductors.ZenerDiode import ZenerDiode
from .Semiconductors.BJT import BJT, BJTType
from .Semiconductors.MOSFET import MOSFET, MOSFETType
from .Magnetic.Transformer import Transformer
from .Sources.VoltageSource import VoltageSource, DCVoltageSource, ACVoltageSource
from .ICs.OpAmp import OpAmp
from .ICs.Comparator import Comparator


# =====================================================================
#  Power Sources
# =====================================================================

def DC5V(name: str, nodes: tuple[Node, Node]) -> VoltageSource:
    """5 V DC supply.  ``nodes = (positive, negative)``."""
    return DCVoltageSource(name, nodes, voltage=5.0)


def DC12V(name: str, nodes: tuple[Node, Node]) -> VoltageSource:
    """12 V DC supply."""
    return DCVoltageSource(name, nodes, voltage=12.0)


def DC24V(name: str, nodes: tuple[Node, Node]) -> VoltageSource:
    """24 V DC supply."""
    return DCVoltageSource(name, nodes, voltage=24.0)


def DC3V3(name: str, nodes: tuple[Node, Node]) -> VoltageSource:
    """3.3 V DC supply."""
    return DCVoltageSource(name, nodes, voltage=3.3)


def AC240V_50Hz(name: str, nodes: tuple[Node, Node]) -> VoltageSource:
    """240 V RMS, 50 Hz mains supply (peak ≈ 339.4 V)."""
    return ACVoltageSource(name, nodes, amplitude=240.0 * 1.41421356, frequency=50.0)


def AC120V_60Hz(name: str, nodes: tuple[Node, Node]) -> VoltageSource:
    """120 V RMS, 60 Hz mains supply (peak ≈ 169.7 V)."""
    return ACVoltageSource(name, nodes, amplitude=120.0 * 1.41421356, frequency=60.0)


# =====================================================================
#  Standard Resistors (E24 + common values)
# =====================================================================

def R10(name: str, nodes: tuple[Node, Node]) -> Resistor:
    """10 Ω resistor."""
    return Resistor(name, nodes, resistance=10.0)


def R100(name: str, nodes: tuple[Node, Node]) -> Resistor:
    """100 Ω resistor."""
    return Resistor(name, nodes, resistance=100.0)


def R220(name: str, nodes: tuple[Node, Node]) -> Resistor:
    """220 Ω resistor."""
    return Resistor(name, nodes, resistance=220.0)


def R330(name: str, nodes: tuple[Node, Node]) -> Resistor:
    """330 Ω resistor."""
    return Resistor(name, nodes, resistance=330.0)


def R470(name: str, nodes: tuple[Node, Node]) -> Resistor:
    """470 Ω resistor."""
    return Resistor(name, nodes, resistance=470.0)


def R1k(name: str, nodes: tuple[Node, Node]) -> Resistor:
    """1 kΩ resistor."""
    return Resistor(name, nodes, resistance=1e3)


def R2k2(name: str, nodes: tuple[Node, Node]) -> Resistor:
    """2.2 kΩ resistor."""
    return Resistor(name, nodes, resistance=2.2e3)


def R4k7(name: str, nodes: tuple[Node, Node]) -> Resistor:
    """4.7 kΩ resistor."""
    return Resistor(name, nodes, resistance=4.7e3)


def R5k(name: str, nodes: tuple[Node, Node]) -> Resistor:
    """5 kΩ resistor."""
    return Resistor(name, nodes, resistance=5e3)


def R10k(name: str, nodes: tuple[Node, Node]) -> Resistor:
    """10 kΩ resistor."""
    return Resistor(name, nodes, resistance=10e3)


def R22k(name: str, nodes: tuple[Node, Node]) -> Resistor:
    """22 kΩ resistor."""
    return Resistor(name, nodes, resistance=22e3)


def R47k(name: str, nodes: tuple[Node, Node]) -> Resistor:
    """47 kΩ resistor."""
    return Resistor(name, nodes, resistance=47e3)


def R100k(name: str, nodes: tuple[Node, Node]) -> Resistor:
    """100 kΩ resistor."""
    return Resistor(name, nodes, resistance=100e3)


def R1M(name: str, nodes: tuple[Node, Node]) -> Resistor:
    """1 MΩ resistor."""
    return Resistor(name, nodes, resistance=1e6)


# =====================================================================
#  Standard Capacitors
# =====================================================================

def C100p(name: str, nodes: tuple[Node, Node]) -> Capacitor:
    """100 pF capacitor."""
    return Capacitor(name, nodes, capacitance=100e-12)


def C1n(name: str, nodes: tuple[Node, Node]) -> Capacitor:
    """1 nF capacitor."""
    return Capacitor(name, nodes, capacitance=1e-9)


def C10n(name: str, nodes: tuple[Node, Node]) -> Capacitor:
    """10 nF capacitor."""
    return Capacitor(name, nodes, capacitance=10e-9)


def C100n(name: str, nodes: tuple[Node, Node]) -> Capacitor:
    """100 nF (0.1 µF) capacitor — common decoupling cap."""
    return Capacitor(name, nodes, capacitance=100e-9)


def C1u(name: str, nodes: tuple[Node, Node]) -> Capacitor:
    """1 µF capacitor."""
    return Capacitor(name, nodes, capacitance=1e-6)


def C10u(name: str, nodes: tuple[Node, Node]) -> Capacitor:
    """10 µF capacitor."""
    return Capacitor(name, nodes, capacitance=10e-6)


def C100u(name: str, nodes: tuple[Node, Node]) -> Capacitor:
    """100 µF electrolytic capacitor."""
    return Capacitor(name, nodes, capacitance=100e-6)


def C470u(name: str, nodes: tuple[Node, Node]) -> Capacitor:
    """470 µF electrolytic capacitor."""
    return Capacitor(name, nodes, capacitance=470e-6)


def C1000u(name: str, nodes: tuple[Node, Node]) -> Capacitor:
    """1000 µF electrolytic capacitor — common PSU filter."""
    return Capacitor(name, nodes, capacitance=1000e-6)


# =====================================================================
#  Rectifier Diodes
# =====================================================================

def IN4001(name: str, nodes: tuple[Node, Node]) -> Diode:
    """
    1N4001 — general-purpose rectifier (50 V, 1 A).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=2.55e-9, n=1.75)


def IN4007(name: str, nodes: tuple[Node, Node]) -> Diode:
    """
    1N4007 — general-purpose rectifier (1000 V, 1 A).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=7.02e-9, n=1.77)


# =====================================================================
#  Signal / Fast-Switching Diodes
# =====================================================================

def IN4148(name: str, nodes: tuple[Node, Node]) -> Diode:
    """
    1N4148 — fast signal diode (75 V, 200 mA, t_rr ≈ 4 ns).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=2.52e-9, n=1.75)


def IN914(name: str, nodes: tuple[Node, Node]) -> Diode:
    """
    1N914 — fast switching signal diode (functionally same as 1N4148).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=2.52e-9, n=1.75)


# =====================================================================
#  Schottky Diodes
# =====================================================================

def IN5817(name: str, nodes: tuple[Node, Node]) -> Diode:
    """
    1N5817 — Schottky barrier diode (20 V, 1 A, V_f ≈ 0.32 V).

    Low forward voltage makes it ideal for power-supply rectification.
    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=3.19e-5, n=1.05)


def IN5819(name: str, nodes: tuple[Node, Node]) -> Diode:
    """
    1N5819 — Schottky barrier diode (40 V, 1 A, V_f ≈ 0.34 V).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=2.5e-5, n=1.05)


def BAT54(name: str, nodes: tuple[Node, Node]) -> Diode:
    """
    BAT54 — small-signal Schottky (30 V, 200 mA, V_f ≈ 0.24 V).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=1.0e-5, n=1.03)


# =====================================================================
#  Zener Diodes (voltage regulation)
# =====================================================================

def BZX55C3V3(name: str, nodes: tuple[Node, Node]) -> ZenerDiode:
    """
    BZX55C3V3 — 3.3 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=3.3, Is=1e-14, Ibv=5e-3, n_bv=1.0)


def BZX55C5V1(name: str, nodes: tuple[Node, Node]) -> ZenerDiode:
    """
    BZX55C5V1 — 5.1 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=5.1, Is=1e-14, Ibv=5e-3, n_bv=1.0)


def BZX55C6V2(name: str, nodes: tuple[Node, Node]) -> ZenerDiode:
    """
    BZX55C6V2 — 6.2 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=6.2, Is=1e-14, Ibv=5e-3, n_bv=1.0)


def BZX55C12(name: str, nodes: tuple[Node, Node]) -> ZenerDiode:
    """
    BZX55C12 — 12 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=12.0, Is=1e-14, Ibv=1e-3, n_bv=1.0)


def BZX55C15(name: str, nodes: tuple[Node, Node]) -> ZenerDiode:
    """
    BZX55C15 — 15 V Zener diode (500 mW).

    ``nodes = (anode, cathode)``
    """
    return ZenerDiode(name, nodes, Vz=15.0, Is=1e-14, Ibv=1e-3, n_bv=1.0)


# Aliases — common shorthand
Zener3V3 = BZX55C3V3
Zener5V1 = BZX55C5V1
Zener6V2 = BZX55C6V2
Zener12V = BZX55C12
Zener15V = BZX55C15


# =====================================================================
#  LEDs
# =====================================================================

def LED_Red(name: str, nodes: tuple[Node, Node]) -> Diode:
    """
    Standard red LED (V_f ≈ 1.8 V, 20 mA typical).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=1.2e-20, n=1.8)


def LED_Green(name: str, nodes: tuple[Node, Node]) -> Diode:
    """
    Standard green LED (V_f ≈ 2.1 V, 20 mA typical).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=1.0e-22, n=1.9)


def LED_Blue(name: str, nodes: tuple[Node, Node]) -> Diode:
    """
    Standard blue/white LED (V_f ≈ 3.2 V, 20 mA typical).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=1.0e-30, n=2.1)


def LED_Yellow(name: str, nodes: tuple[Node, Node]) -> Diode:
    """
    Standard yellow LED (V_f ≈ 2.0 V, 20 mA typical).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=5.0e-22, n=1.85)


def LED_White(name: str, nodes: tuple[Node, Node]) -> Diode:
    """
    Standard white LED (V_f ≈ 3.2 V, 20 mA typical).

    ``nodes = (anode, cathode)``
    """
    return Diode(name, nodes, Is=1.0e-30, n=2.1)


# =====================================================================
#  NPN Transistors
# =====================================================================
#
# All BJTs:  nodes = (collector, base, emitter)
#

def N2N2222(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    2N2222 — general-purpose fast-switching NPN (40 V, 800 mA).

    Typical Ic(max) = 800 mA, BF = 100–300, f_T = 300 MHz.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=14.34e-15, BF=255.9, BR=6.092, Nf=1.0, Nr=1.0, Vaf=74.03)


def BC547(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    BC547 — general-purpose small-signal NPN (45 V, 100 mA).

    Very popular in Europe/Asia for amplifiers and switching.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.8e-14, BF=400.0, BR=35.5, Nf=1.0, Nr=1.0, Vaf=80.0)


def BC548(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    BC548 — general-purpose small-signal NPN (30 V, 100 mA).

    Similar to BC547 with lower Vceo.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.8e-14, BF=400.0, BR=35.5, Nf=1.0, Nr=1.0, Vaf=80.0)


def BC549(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    BC549 — low-noise small-signal NPN (30 V, 100 mA).

    Preferred over BC547/548 for audio pre-amp stages.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.8e-14, BF=420.0, BR=35.5, Nf=1.0, Nr=1.0, Vaf=80.0)


def N2N3904(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    2N3904 — general-purpose low-power NPN (40 V, 200 mA).

    One of the most commonly available transistors worldwide.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=6.734e-15, BF=416.4, BR=0.7389, Nf=1.0, Nr=1.0, Vaf=74.03)


def TIP31C(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    TIP31C — medium-power NPN (100 V, 3 A, 40 W).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.0e-12, BF=50.0, BR=4.0, Nf=1.0, Nr=1.0, Vaf=100.0)


def TIP41C(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    TIP41C — high-power NPN (100 V, 6 A, 65 W).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.0e-12, BF=60.0, BR=4.0, Nf=1.0, Nr=1.0, Vaf=100.0)


def N2N3055(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    2N3055 — classic high-power NPN (60 V, 15 A, 115 W).

    Iconic power transistor for linear supplies and audio.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=2.0e-11, BF=50.0, BR=4.0, Nf=1.0, Nr=1.0, Vaf=100.0)


def BD139(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    BD139 — medium-power NPN (80 V, 1.5 A, 12.5 W).

    Popular for audio driver stages.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.0e-13, BF=100.0, BR=5.0, Nf=1.0, Nr=1.0, Vaf=80.0)


def S8050(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    S8050 — low-voltage, high-current NPN (25 V, 1.5 A).

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.0e-14, BF=200.0, BR=5.0, Nf=1.0, Nr=1.0, Vaf=50.0)


# =====================================================================
#  PNP Transistors
# =====================================================================

def N2N3906(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    2N3906 — general-purpose low-power PNP (40 V, 200 mA).

    Complementary pair to 2N3904.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=1.305e-14, BF=180.7, BR=4.977, Nf=1.0, Nr=1.0, Vaf=18.7)


def BC557(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    BC557 — general-purpose small-signal PNP (45 V, 100 mA).

    Complementary to BC547.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=1.8e-14, BF=330.0, BR=35.0, Nf=1.0, Nr=1.0, Vaf=60.0)


def BC558(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    BC558 — general-purpose small-signal PNP (30 V, 100 mA).

    Complementary to BC548.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=1.8e-14, BF=330.0, BR=35.0, Nf=1.0, Nr=1.0, Vaf=60.0)


def N2N2907(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    2N2907 — general-purpose PNP (60 V, 600 mA).

    Complementary to 2N2222.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=6.5e-15, BF=200.0, BR=4.0, Nf=1.0, Nr=1.0, Vaf=115.0)


def TIP32C(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    TIP32C — medium-power PNP (100 V, 3 A, 40 W).

    Complementary to TIP31C.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=1.0e-12, BF=50.0, BR=4.0, Nf=1.0, Nr=1.0, Vaf=100.0)


def TIP42C(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    TIP42C — high-power PNP (100 V, 6 A, 65 W).

    Complementary to TIP41C.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=1.0e-12, BF=60.0, BR=4.0, Nf=1.0, Nr=1.0, Vaf=100.0)


def BD140(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    BD140 — medium-power PNP (80 V, 1.5 A, 12.5 W).

    Complementary to BD139.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=1.0e-13, BF=100.0, BR=5.0, Nf=1.0, Nr=1.0, Vaf=80.0)


def S8550(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    S8550 — low-voltage, high-current PNP (25 V, 1.5 A).

    Complementary to S8050.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=1.0e-14, BF=200.0, BR=5.0, Nf=1.0, Nr=1.0, Vaf=50.0)


# =====================================================================
#  Darlington Transistors (High Gain)
# =====================================================================

def TIP120(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    TIP120 — NPN Darlington (60 V, 5 A, 65 W), hFE ≥ 1000.

    Commonly used to switch heavy loads from microcontroller pins.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=6.8e-10, BF=1000.0, BR=10.0, Nf=1.5, Nr=1.0, Vaf=100.0)


def TIP125(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    TIP125 — PNP Darlington (60 V, 5 A, 65 W), hFE ≥ 1000.

    PNP complement of TIP120.
    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.PNP,
               Is=6.8e-10, BF=1000.0, BR=10.0, Nf=1.5, Nr=1.0, Vaf=100.0)


def N2N5306(name: str, nodes: tuple[Node, Node, Node]) -> BJT:
    """
    2N5306 — high-gain small-signal NPN Darlington.

    ``nodes = (collector, base, emitter)``
    """
    return BJT(name, nodes, BJTType.NPN,
               Is=1.0e-10, BF=2500.0, BR=10.0, Nf=1.5, Nr=1.0, Vaf=100.0)


# =====================================================================
#  Transformers (240 V mains, 50 Hz)
# =====================================================================
#
# Turns ratio  n = √(L_primary / L_secondary)
# For a 240 → V_out transformer:  L_sec = L_prim × (V_out / 240)²
# Using L_prim = 100 H as reference.
#

def Transformer_240_to_5(
    name: str,
    primary_nodes: tuple[Node, Node],
    secondary_nodes: tuple[Node, Node],
) -> Transformer:
    """
    240 V → 5 V step-down transformer (turns ratio ≈ 48:1).

    ``primary_nodes = (p+, p−)``, ``secondary_nodes = (s+, s−)``
    """
    # L_sec = 100 * (5/240)² ≈ 0.0434 H
    return Transformer(name, primary_nodes, secondary_nodes,
                       primary_inductance=100.0,
                       secondary_inductance=0.0434,
                       k=0.999)


def Transformer_240_to_12(
    name: str,
    primary_nodes: tuple[Node, Node],
    secondary_nodes: tuple[Node, Node],
) -> Transformer:
    """
    240 V → 12 V step-down transformer (turns ratio = 20:1).

    ``primary_nodes = (p+, p−)``, ``secondary_nodes = (s+, s−)``
    """
    # L_sec = 100 * (12/240)² = 0.25 H
    return Transformer(name, primary_nodes, secondary_nodes,
                       primary_inductance=100.0,
                       secondary_inductance=0.25,
                       k=0.999)


def Transformer_240_to_24(
    name: str,
    primary_nodes: tuple[Node, Node],
    secondary_nodes: tuple[Node, Node],
) -> Transformer:
    """
    240 V → 24 V step-down transformer (turns ratio = 10:1).

    ``primary_nodes = (p+, p−)``, ``secondary_nodes = (s+, s−)``
    """
    # L_sec = 100 * (24/240)² = 1.0 H
    return Transformer(name, primary_nodes, secondary_nodes,
                       primary_inductance=100.0,
                       secondary_inductance=1.0,
                       k=0.999)


# =====================================================================
#  Operational Amplifiers  (non_inv_input, inv_input, output)
# =====================================================================

def LM741(
    name: str,
    nodes: tuple[Node, Node, Node],
) -> OpAmp:
    """
    LM741 — general-purpose op-amp.

    A_OL ≈ 200 000 (106 dB), R_in ≈ 2 MΩ, R_out ≈ 75 Ω.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=200_000.0, R_in=2e6, R_out=75.0)


def LM358(
    name: str,
    nodes: tuple[Node, Node, Node],
) -> OpAmp:
    """
    LM358 — dual general-purpose op-amp (single-supply capable).

    A_OL ≈ 100 000 (100 dB), R_in ≈ 2 MΩ, R_out ≈ 150 Ω.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=100_000.0, R_in=2e6, R_out=150.0)


def LM324(
    name: str,
    nodes: tuple[Node, Node, Node],
) -> OpAmp:
    """
    LM324 — quad general-purpose op-amp (single-supply capable).

    A_OL ≈ 100 000 (100 dB), R_in ≈ 2 MΩ, R_out ≈ 150 Ω.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=100_000.0, R_in=2e6, R_out=150.0)


def TL072(
    name: str,
    nodes: tuple[Node, Node, Node],
) -> OpAmp:
    """
    TL072 — low-noise JFET-input dual op-amp.

    A_OL ≈ 200 000 (106 dB), R_in ≈ 1 TΩ, R_out ≈ 100 Ω.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=200_000.0, R_in=1e12, R_out=100.0)


def TL082(
    name: str,
    nodes: tuple[Node, Node, Node],
) -> OpAmp:
    """
    TL082 — general-purpose JFET-input dual op-amp.

    A_OL ≈ 200 000 (106 dB), R_in ≈ 1 TΩ, R_out ≈ 100 Ω.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=200_000.0, R_in=1e12, R_out=100.0)


def NE5532(
    name: str,
    nodes: tuple[Node, Node, Node],
) -> OpAmp:
    """
    NE5532 — low-noise audio dual op-amp.

    A_OL ≈ 100 000 (100 dB), R_in ≈ 300 kΩ, R_out ≈ 0.3 Ω.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=100_000.0, R_in=300e3, R_out=0.3)


def OP07(
    name: str,
    nodes: tuple[Node, Node, Node],
) -> OpAmp:
    """
    OP07 — ultra-low-offset precision op-amp.

    A_OL ≈ 500 000 (114 dB), R_in ≈ 33 MΩ, R_out ≈ 60 Ω.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=500_000.0, R_in=33e6, R_out=60.0)


def OPA2134(
    name: str,
    nodes: tuple[Node, Node, Node],
) -> OpAmp:
    """
    OPA2134 — high-performance audio dual op-amp (FET input).

    A_OL ≈ 1 000 000 (120 dB), R_in ≈ 10 TΩ, R_out ≈ 1 Ω.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=1_000_000.0, R_in=10e12, R_out=1.0)


def AD620(
    name: str,
    nodes: tuple[Node, Node, Node],
) -> OpAmp:
    """
    AD620 — low-cost instrumentation amplifier (modelled as single op-amp).

    A_OL ≈ 1 000 000 (120 dB), R_in ≈ 10 GΩ, R_out ≈ 1 Ω.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return OpAmp(name, nodes, A_OL=1_000_000.0, R_in=10e9, R_out=1.0)


def IdealOpAmp(
    name: str,
    nodes: tuple[Node, Node, Node],
) -> OpAmp:
    """
    Ideal op-amp — very high gain, near-infinite input impedance,
    near-zero output impedance.

    ``nodes = (non_inv_input, inv_input, output)``

    A_OL = 10⁹, R_in = 10¹² Ω, R_out ≈ 0 Ω.
    """
    return OpAmp(name, nodes, A_OL=1e9, R_in=1e12, R_out=0.001)


# =====================================================================
#  Comparators  (non_inv_input, inv_input, output)
# =====================================================================

def LM393(
    name: str,
    nodes: tuple[Node, Node, Node],
    *,
    V_high: float = 5.0,
    V_low: float = 0.0,
) -> Comparator:
    """
    LM393 — dual open-collector comparator.

    R_in ≈ 200 kΩ, R_out ≈ 50 Ω (modelled as push-pull here).

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return Comparator(name, nodes,
                      V_high=V_high, V_low=V_low,
                      R_in=200e3, R_out=50.0)


def LM339(
    name: str,
    nodes: tuple[Node, Node, Node],
    *,
    V_high: float = 5.0,
    V_low: float = 0.0,
) -> Comparator:
    """
    LM339 — quad open-collector comparator.

    R_in ≈ 200 kΩ, R_out ≈ 50 Ω.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return Comparator(name, nodes,
                      V_high=V_high, V_low=V_low,
                      R_in=200e3, R_out=50.0)


def LM311(
    name: str,
    nodes: tuple[Node, Node, Node],
    *,
    V_high: float = 5.0,
    V_low: float = 0.0,
) -> Comparator:
    """
    LM311 — single high-speed comparator.

    R_in ≈ 400 kΩ, R_out ≈ 30 Ω.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return Comparator(name, nodes,
                      V_high=V_high, V_low=V_low,
                      R_in=400e3, R_out=30.0)


def TLV3201(
    name: str,
    nodes: tuple[Node, Node, Node],
    *,
    V_high: float = 3.3,
    V_low: float = 0.0,
) -> Comparator:
    """
    TLV3201 — single low-power push-pull comparator (3.3 V / 5 V).

    R_in ≈ 1 MΩ, R_out ≈ 30 Ω.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return Comparator(name, nodes,
                      V_high=V_high, V_low=V_low,
                      R_in=1e6, R_out=30.0)


def MAX9021(
    name: str,
    nodes: tuple[Node, Node, Node],
    *,
    V_high: float = 3.3,
    V_low: float = 0.0,
) -> Comparator:
    """
    MAX9021 — single nano-power push-pull comparator (1.8–5.5 V).

    R_in ≈ 1 MΩ, R_out ≈ 40 Ω.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return Comparator(name, nodes,
                      V_high=V_high, V_low=V_low,
                      R_in=1e6, R_out=40.0)


def IdealComparator(
    name: str,
    nodes: tuple[Node, Node, Node],
    *,
    V_high: float = 5.0,
    V_low: float = 0.0,
) -> Comparator:
    """
    Ideal comparator — no delay, infinite input impedance,
    near-zero output resistance.

    ``nodes = (non_inv_input, inv_input, output)``
    """
    return Comparator(name, nodes,
                      V_high=V_high, V_low=V_low,
                      R_in=1e12, R_out=0.001)
