# aero

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)

A small, dependency-light Python library of common aerospace engineering
calculations — standard atmosphere, aerodynamics, orbital mechanics,
rocketry and great-circle navigation — plus read-only clients for public
space-agency data services (NASA, ESA, ISS and ISRO).

The calculation helpers are pure Python with type hints and use SI units,
except that `aero.navigation` takes latitude, longitude and bearings in
degrees (and `central_angle` returns radians). The data-service clients
perform HTTP requests and return the provider's payload as-is, so their
values are in whatever units the service publishes. Everything is covered
by tests.

## Contents

- [Installation](#installation)
- [Quick start](#quick-start)
- [Modules](#modules)
  - [Calculation modules](#calculation-modules)
  - [Data-service clients](#data-service-clients)
- [Units and conventions](#units-and-conventions)
- [Project layout](#project-layout)
- [Connecting to NASA programs](#connecting-to-nasa-programs)
- [Connecting to European space programs](#connecting-to-european-space-programs)
- [Connecting to International Space Station programs](#connecting-to-international-space-station-programs)
- [Connecting to ISRO programs](#connecting-to-isro-programs)
- [Error handling](#error-handling)
- [Website](#website)
- [Running tests](#running-tests)
- [License](#license)

## Installation

Python 3.8 or newer is required. The only runtime dependency is
[`requests`](https://pypi.org/project/requests/), used by the data-service
clients.

```bash
git clone https://github.com/charles2ke/aero.git
cd aero
pip install -e .
```

## Quick start

```python
from aero import atmosphere, aerodynamics, navigation, orbital, rocketry

# Standard atmosphere at 5000 m altitude
rho = atmosphere.density(5000)
a = atmosphere.speed_of_sound(5000)

# Lift produced by a wing
L = aerodynamics.lift(rho=rho, velocity=120.0, area=16.2, cl=0.4)

# Circular low Earth orbit velocity at 400 km altitude
v = orbital.circular_orbital_velocity(orbital.EARTH_MU, orbital.EARTH_RADIUS + 400_000)

# Ideal delta-v of a stage with a 300 s specific impulse engine
ve = rocketry.exhaust_velocity(300.0)
dv = rocketry.delta_v(ve, initial_mass=5500.0, final_mass=1500.0)

# Liftoff thrust-to-weight ratio
twr = rocketry.thrust_to_weight_ratio(thrust_force=7_600_000.0, mass=549_054.0)

# Shortest path (great circle) from New York JFK to London Heathrow
distance = navigation.great_circle_distance(40.6413, -73.7781, 51.4700, -0.4543)
course = navigation.initial_bearing(40.6413, -73.7781, 51.4700, -0.4543)
route = navigation.shortest_path(40.6413, -73.7781, 51.4700, -0.4543, segments=8)
```

## Modules

### Calculation modules

| Module | What it provides |
| --- | --- |
| `aero.atmosphere` | International Standard Atmosphere (ISA) model: `temperature`, `pressure`, `density`, `speed_of_sound`, valid up to 20 km. |
| `aero.aerodynamics` | `dynamic_pressure`, `lift`, `drag`, `lift_to_drag_ratio`, `mach_number`, `reynolds_number`. |
| `aero.orbital` | `orbital_velocity` (vis-viva), `circular_orbital_velocity`, `orbital_period`, `escape_velocity`, plus `EARTH_MU` and `EARTH_RADIUS`. |
| `aero.rocketry` | Tsiolkovsky rocket equation (`delta_v`), `mass_ratio`, `propellant_mass`, `specific_impulse`/`exhaust_velocity`, `thrust`, `mass_flow_rate`, `burn_time`, `thrust_to_weight_ratio`, and multi-stage budgets (`stage_delta_v`, `total_delta_v`). |
| `aero.navigation` | Great-circle navigation over a spherical Earth: `central_angle`, `great_circle_distance`, `initial_bearing`, `final_bearing`, `destination_point`, `intermediate_point`, `shortest_path`. |

### Data-service clients

| Module | Client | Services covered |
| --- | --- | --- |
| `aero.nasa` | `NASAClient` | NASA Open APIs: APOD, Mars Rover Photos, NeoWs, DONKI, EPIC, InSight Mars weather, TechPort, Exoplanet Archive. |
| `aero.esa` | `ESAClient` | ESA Open Data Portal, Copernicus Data Space Ecosystem (Sentinel products), Gaia Archive, NEOCC near-Earth object risk list. |
| `aero.iss` | `ISSClient` | Open Notify (ISS position, people in space), "Where the ISS at?" (state vectors, propagated positions, TLEs), CelesTrak elements for the ISS and the `stations` group. |
| `aero.isro` | `ISROClient` | ISRO API (spacecraft, launchers, customer satellites, centres), ISRO launch records from Launch Library 2, CelesTrak elements for ISRO spacecraft including NavIC (IRNSS). |

Only the NASA client uses an API key; the ESA, ISS and ISRO services are
read-only and need no account.

## Units and conventions

- All calculations use **SI units**: metres, seconds, kilograms, kelvin,
  pascals, newtons.
- Altitudes are geopotential altitudes above mean sea level; the ISA model
  is defined up to 20 km.
- Latitudes and longitudes are in **degrees** (latitude in `[-90, 90]`,
  longitude in `[-180, 360]`); bearings are degrees clockwise from true
  north in `[0, 360)`.
- Invalid inputs (for example a negative mass ratio or an out-of-range
  latitude) raise `ValueError`.

## Project layout

```
aero/       library modules (calculations and data-service clients)
tests/      pytest suite, with HTTP calls stubbed out
website/    static site: module docs, calculators and data explorer
```

## Connecting to NASA programs

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

## Connecting to European space programs

`aero.esa.ESAClient` provides connectivity to public European Space
Agency (ESA) data services. None of these read-only endpoints require an
API key or account.

```python
from aero import esa

client = esa.ESAClient()

client.open_data_search(query="satellite")          # ESA Open Data Portal
client.copernicus_products(collection="SENTINEL-2")  # Copernicus Sentinel products
client.gaia_query("select top 10 * from gaiadr3.gaia_source")  # Gaia Archive
client.neocc_risk_list()                              # NEOCC risk list
```

## Connecting to International Space Station programs

`aero.iss.ISSClient` provides connectivity to public International Space
Station data services. None of these read-only endpoints require an API key
or account.

```python
from aero import iss

client = iss.ISSClient()

client.current_location()                    # Open Notify: ISS ground track point
client.people_in_space()                     # Open Notify: crew currently in orbit
client.satellite_position()                  # Where the ISS at?: ISS state vector
client.satellite_positions([1436029892])     # Where the ISS at?: propagated positions
client.tle()                                 # Where the ISS at?: latest ISS TLE
client.celestrak_elements()                  # CelesTrak: ISS orbital elements
client.station_elements()                    # CelesTrak: all "stations" group objects
```

## Connecting to ISRO programs

`aero.isro.ISROClient` provides connectivity to public Indian Space
Research Organisation (ISRO) data services. None of these read-only
endpoints require an API key or account.

```python
from aero import isro

client = isro.ISROClient()

client.spacecrafts()                     # ISRO API: spacecraft and satellites
client.launchers()                       # ISRO API: launch vehicles
client.customer_satellites()             # ISRO API: customer satellites launched
client.centres()                         # ISRO API: ISRO centres and units
client.launches(limit=10)                # Launch Library 2: past ISRO launches
client.launches(upcoming=True)           # Launch Library 2: upcoming ISRO launches
client.agency()                          # Launch Library 2: ISRO agency metadata
client.celestrak_elements(norad_id=41384)  # CelesTrak: elements for one spacecraft
client.navic_elements()                  # CelesTrak: NavIC (IRNSS) constellation
```

## Error handling

Each client raises its own `RuntimeError` subclass — `NASAAPIError`,
`ESAAPIError`, `ISSAPIError`, `ISROAPIError` — when a request fails or the
service returns a non-OK response. Every client also accepts an injectable
`requests.Session` and a `timeout` (seconds), which is handy for retries,
proxies, custom headers and testing.

```python
import requests
from aero import iss

client = iss.ISSClient(session=requests.Session(), timeout=10)

try:
    position = client.current_location()
except iss.ISSAPIError as exc:
    print(f"ISS service unavailable: {exc}")
```

## Website

A static website for the project lives in [`website/`](website/). It
documents every module and lets you try them all from the browser:

- Calculators reproduce the `atmosphere`, `aerodynamics`, `orbital`,
  `rocketry` and `navigation` formulas implemented in the library.
- A data-service explorer builds the exact request each `nasa`, `esa`,
  `iss` and `isro` client method sends, shows the equivalent Python
  snippet, and can send the request live from the browser (services that
  block cross-origin requests can be opened in a new tab instead).
- Every code block and generated snippet has a one-click copy button.
- Subtle entrance and hover animations, automatically disabled for
  visitors who prefer reduced motion.

Open `website/index.html` directly, or serve the folder:

```bash
python -m http.server --directory website 8000
```

### Publishing to GitHub Pages

The website is published to GitHub Pages by the
[`Deploy website to GitHub Pages`](.github/workflows/pages.yml) workflow,
which runs on pushes to `main` that touch `website/` and can also be
triggered manually from the Actions tab. To enable it, set
**Settings → Pages → Build and deployment → Source** to **GitHub Actions**.
The published site is then available at
`https://charles2ke.github.io/aero/`.

## Running tests

```bash
pip install pytest
pytest
```

The library tests stub out HTTP calls, so no network access or API key is
needed to run them.

The website tests use Playwright and are skipped unless it is installed:

```bash
pip install playwright
playwright install chromium
pytest tests/test_website.py
```

## License

Released under the [MIT License](LICENSE).
