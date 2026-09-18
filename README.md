# aero
Aerospace Engineering

A small Python library of common aerospace engineering calculations:

- `aero.atmosphere` — International Standard Atmosphere (ISA) model
  (temperature, pressure, density, and speed of sound up to 20 km).
- `aero.aerodynamics` — dynamic pressure, lift, drag, lift-to-drag ratio,
  Mach number, and Reynolds number.
- `aero.orbital` — orbital mechanics helpers (vis-viva orbital velocity,
  circular orbital velocity, orbital period, and escape velocity).

## Installation

```bash
pip install -e .
```

## Usage

```python
from aero import atmosphere, aerodynamics, orbital

# Standard atmosphere at 5000 m altitude
rho = atmosphere.density(5000)
a = atmosphere.speed_of_sound(5000)

# Lift produced by a wing
L = aerodynamics.lift(rho=rho, velocity=120.0, area=16.2, cl=0.4)

# Circular low Earth orbit velocity at 400 km altitude
v = orbital.circular_orbital_velocity(orbital.EARTH_MU, orbital.EARTH_RADIUS + 400_000)
```

## Running tests

```bash
pip install pytest
pytest
```
