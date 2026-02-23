"""
Pre-built component library — real-world parts with datasheet values.

Every factory function takes only a **name** and **nodes** tuple, returns a
ready-to-use component instance.  No need to look up datasheet parameters.

Each function is explicitly typed so IDEs can provide full autocomplete,
parameter hints, and return-type resolution.

Usage::

    from PyEEL.Components.library import R1k, IN4007, BC547, IRF540N

    ckt.AddComponent(R1k("R1", (n1, n2)))
    ckt.AddComponent(IN4007("D1", (n_a, n_k)))
    ckt.AddComponent(BC547("Q1", (n_c, n_b, n_e)))
    ckt.AddComponent(IRF540N("M1", (n_d, n_g, n_s)))

Sub-modules::

    library.sources      — DC and AC supply presets
    library.resistors    — Standard resistor values (E24+)
    library.capacitors   — Standard capacitor values
    library.inductors    — Standard inductor values
    library.diodes       — Rectifiers, signal, Schottky, LEDs
    library.zener_diodes — Zener diode series + aliases
    library.bjt          — NPN, PNP, and Darlington transistors
    library.mosfets      — N-channel and P-channel MOSFETs
    library.transformers — Mains step-down transformer presets
    library.opamps       — Operational amplifiers
    library.comparators  — Voltage comparators
"""

# ── Sources ─────────────────────────────────────────────────────────
from .sources import (
    DC3V3, DC5V, DC9V, DC12V, DC15V, DC24V, DC48V,
    AC240V_50Hz, AC230V_50Hz, AC120V_60Hz, AC100V_50Hz,
)

# ── Passive ─────────────────────────────────────────────────────────
from .resistors import (
    R10, R22, R47, R100, R150, R220, R330, R470, R680,
    R1k, R1k5, R2k2, R3k3, R4k7, R5k, R6k8,
    R10k, R15k, R22k, R33k, R47k, R56k, R68k,
    R100k, R220k, R470k, R1M, R10M,
)

from .capacitors import (
    C10p, C22p, C47p, C100p, C220p,
    C1n, C10n, C22n, C47n, C100n,
    C1u, C2u2, C4u7, C10u, C22u, C47u,
    C100u, C220u, C470u, C1000u, C2200u, C4700u,
)

from .inductors import (
    L1u, L4u7, L10u, L22u, L47u, L100u, L220u, L470u,
    L1m, L2m2, L4m7, L10m, L22m, L47m, L100m,
    L1H, L10H,
)

# ── Diodes ──────────────────────────────────────────────────────────
from .diodes import (
    # Rectifier
    IN4001, IN4002, IN4004, IN4007, IN5399, IN5408,
    # Signal
    IN4148, IN914, IN4454,
    # Schottky
    IN5817, IN5819, IN5822, BAT54, BAT46,
    # LEDs
    LED_Red, LED_Orange, LED_Yellow, LED_Green,
    LED_Blue, LED_White, LED_IR, LED_UV,
)

from .zener_diodes import (
    BZX55C2V7, BZX55C3V3, BZX55C3V9, BZX55C4V7,
    BZX55C5V1, BZX55C5V6, BZX55C6V2, BZX55C6V8,
    BZX55C7V5, BZX55C9V1, BZX55C10,
    BZX55C12, BZX55C15, BZX55C18, BZX55C24, BZX55C33,
    # Aliases
    Zener2V7, Zener3V3, Zener3V9, Zener4V7,
    Zener5V1, Zener5V6, Zener6V2, Zener6V8,
    Zener7V5, Zener9V1, Zener10V,
    Zener12V, Zener15V, Zener18V, Zener24V, Zener33V,
)

# ── Transistors ─────────────────────────────────────────────────────
from .bjt import (
    # NPN
    N2N2222, N2N2222A, N2N3904, BC547, BC547B, BC548, BC549,
    BC337, TIP31C, TIP41C, N2N3055, BD139, S8050, MPSA42,
    # PNP
    N2N3906, N2N2907, BC557, BC558,
    TIP32C, TIP42C, BD140, S8550, MPSA92,
    # Darlington
    TIP120, TIP121, TIP122, TIP125, TIP126, TIP127, N2N5306,
)

from .mosfets import (
    # NMOS
    N2N7000, BS170, IRLZ44N, IRF520N, IRF530N, IRF540N,
    IRF640N, IRF840, IRFZ44N, AO3400,
    # PMOS
    IRF9540N, IRF9530N, IRF4905, BS250, AO3401,
)

# ── Transformers ────────────────────────────────────────────────────
from .transformers import (
    Transformer_240_to_5, Transformer_240_to_9,
    Transformer_240_to_12, Transformer_240_to_24, Transformer_240_to_48,
    Transformer_120_to_5, Transformer_120_to_12, Transformer_120_to_24,
)

# ── ICs ─────────────────────────────────────────────────────────────
from .opamps import (
    LM741, LM358, LM324, UA741,
    TL071, TL072, TL074, TL082, TL084,
    NE5532, NE5534, OPA2134, OPA2604,
    OP07, OP27, AD620, INA128,
    IdealOpAmp,
)

from .comparators import (
    LM393, LM339, LM311, LM2903,
    TLV3201, TLV3501, MAX9021, MAX9042,
    IdealComparator,
)
