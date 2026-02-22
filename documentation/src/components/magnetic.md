# Magnetic Components

PyEEL supports coupled inductors and transformers for modelling energy
transfer through magnetic fields.

| Component | Description |
|---|---|
| [Mutual Coupling](mutual-coupling.md) | Couples two existing `Inductor` components with coefficient $k$ |
| [Transformer](transformer.md) | High-level wrapper: two inductors + mutual coupling in one object |

## Import

```python
from PyEEL import MutualCoupling, Transformer
```
