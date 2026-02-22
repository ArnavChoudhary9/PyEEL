# Installation

## Requirements

- **Python ≥ 3.10** (uses `X | Y` union type syntax)
- **NumPy** — dense linear-algebra solver
- **matplotlib** — live plotting

## Install from Source

```bash
git clone https://github.com/ArnavChoudhary9/PyEEL.git
cd PyEEL
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

The `requirements.txt` contains:

```
numpy
matplotlib
```

## Verify

```bash
python -c "from PyEEL import Circuit, NumpySolver; print('PyEEL OK')"
```

## Running Examples

```bash
python examples/half_wave_rectifier.py
python examples/ce_amplifier.py
python examples/linear_power_supply.py
```

Each example opens a real-time matplotlib window. Press **Space** to
pause/resume; close the window to exit.
