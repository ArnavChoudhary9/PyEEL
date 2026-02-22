# Integrated Circuits

Integrated circuit macro models provide higher-level abstractions for
multi-transistor ICs.  Rather than modelling individual transistors,
each IC is represented by a behavioural **macro model** that captures
the key input/output characteristics.

## Available ICs

| Component | Class | Terminals | Description |
|---|---|---|---|
| **Op-Amp** | `OpAmp` | `(V+, V-, Vout)` | Voltage-feedback operational amplifier |

## Adding More ICs

New IC types (comparators, voltage regulators, 555 timers, etc.) can
be added by creating a new class in `PyEEL/Components/ICs/` that
inherits from `Component`.  See
[Adding New Components](../extending/new-components.md) for the
step-by-step guide.
