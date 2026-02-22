# Example: Transformer

A step-down transformer with a resistive load, demonstrating magnetic
coupling and the turns ratio relationship.

**File:** `examples/transformer.py`

## Circuit

```
V_ac ──── R_pri (100Ω) ──── T1 primary ════ T1 secondary ──── R_load (5Ω)
(240V       (winding       (L1=2.304H)    (L2=1mH, k=0.99)   │
 50Hz)       resistance)                                      GND
```

Turns ratio: $n = \sqrt{L_1/L_2} = \sqrt{2.304/0.001} \approx 48:1$

Expected secondary voltage: $V_{sec} \approx 240/48 \approx 5$ V peak.

## Code Highlights

```python
T1 = Transformer("T1",
    primary_nodes=(n_pri, gnd),
    secondary_nodes=(n_sec, gnd),
    primary_inductance=2.304,
    secondary_inductance=1e-3,
    k=0.99,
)
ckt.AddComponent(T1)

# Measure currents through the internal inductors
ckt.AddProbe(CurrentProbe("I_pri", T1.Primary))
ckt.AddProbe(CurrentProbe("I_sec", T1.Secondary))
```

## What to Observe

- The secondary voltage is approximately 48× smaller than the primary.
- The secondary current is approximately 48× larger (power conservation).
- With $k = 0.99$ (not perfect), there is some leakage — the voltage
  ratio is slightly less than ideal.

## Key Concepts Demonstrated

- Transformer constructor with inductance values
- Accessing `T1.Primary` and `T1.Secondary` for current probes
- Relationship between inductance ratio and turns ratio
- Effect of coupling coefficient $k$
