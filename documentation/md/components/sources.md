# Sources

PyEEL provides independent and dependent (controlled) voltage and current
sources.

| Source | Type | Description |
|---|---|---|
| [Voltage Source](voltage-source.md) | Independent | Forces a specified voltage waveform |
| [Dependent Sources](dependent-sources.md) | Controlled | Output depends on a voltage or current elsewhere |

## Import

```python
from PyEEL import (
    VoltageSource, DCVoltageSource, ACVoltageSource,
    Waveform, ConstantWave, SineWave,
    VCVS, VCCS, CCVS, CCCS,
)
```
