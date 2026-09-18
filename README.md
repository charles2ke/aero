# aero
Aerospace Engineering

A small Python library of common aerospace engineering calculations:

- `aero.atmosphere` — International Standard Atmosphere (ISA) model
  (temperature, pressure, density, and speed of sound up to 20 km).
- `aero.aerodynamics` — dynamic pressure, lift, drag, lift-to-drag ratio,
  Mach number, and Reynolds number.
- `aero.orbital` — orbital mechanics helpers (vis-viva orbital velocity,
  circular orbital velocity, orbital period, and escape velocity).
- `aero.nasa` — connectivity to NASA's public Open APIs, covering multiple
  NASA programs: APOD, Mars Rover Photos, NeoWs, DONKI, EPIC, InSight Mars
  weather, TechPort, and the Exoplanet Archive.

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

### Connecting to NASA programs

`aero.nasa.NASAClient` provides connectivity to several NASA Open APIs.
Register a free API key at https://api.nasa.gov/ and set it via the
`NASA_API_KEY` environment variable (or pass `api_key=...` explicitly). If
no key is provided, NASA's rate-limited `DEMO_KEY` is used.

```python
from aero import nasa

client = nasa.NASAClient()  # uses NASA_API_KEY env var, or DEMO_KEY

client.apod()                                  # Astronomy Picture of the Day
client.mars_rover_photos(rover="curiosity", sol=1000)
client.neo_feed(start_date="2024-01-01", end_date="2024-01-02")
client.donki_notifications(start_date="2024-01-01")
client.epic_natural_images()
client.insight_weather()
client.techport_projects()
client.exoplanets(query="select pl_name from ps")  # no API key required
```

## Running tests

```bash
pip install pytest
pytest
```
