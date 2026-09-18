# aero
Aerospace Engineering

A small Python library of common aerospace engineering calculations:

- `aero.atmosphere` — International Standard Atmosphere (ISA) model
  (temperature, pressure, density, and speed of sound up to 20 km).
- `aero.aerodynamics` — dynamic pressure, lift, drag, lift-to-drag ratio,
  Mach number, and Reynolds number.
- `aero.orbital` — orbital mechanics helpers (vis-viva orbital velocity,
  circular orbital velocity, orbital period, and escape velocity).
- `aero.rocketry` — rocket science: the Tsiolkovsky rocket equation,
  mass ratios, propellant sizing, specific impulse and exhaust velocity,
  thrust and mass flow, burn time, thrust-to-weight ratio, and multi-stage
  delta-v budgets.
- `aero.nasa` — connectivity to NASA's public Open APIs, covering multiple
  NASA programs: APOD, Mars Rover Photos, NeoWs, DONKI, EPIC, InSight Mars
  weather, TechPort, and the Exoplanet Archive.
- `aero.esa` — connectivity to public European Space Agency (ESA) data
  services: the ESA Open Data Portal, the Copernicus Data Space Ecosystem
  (Sentinel products), the Gaia Archive, and the NEOCC near-Earth object
  risk list.
- `aero.iss` — connectivity to International Space Station program data
  services: Open Notify (ISS position, people in space), "Where the ISS
  at?" (state vectors, position propagation, TLEs), and CelesTrak orbital
  elements for the ISS and the `stations` group.
- `aero.isro` — connectivity to Indian Space Research Organisation (ISRO)
  data services: the public ISRO API (spacecraft, launchers, customer
  satellites, centres), ISRO launch records from Launch Library 2, and
  CelesTrak orbital elements for ISRO spacecraft including NavIC (IRNSS).

## Installation

```bash
pip install -e .
```

## Usage

```python
from aero import atmosphere, aerodynamics, orbital, rocketry

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

### Connecting to European space programs

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

### Connecting to International Space Station programs

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

### Connecting to ISRO programs

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

## Website

A static website for the project lives in [`website/`](website/). It
documents every module and lets you try them all from the browser:

- Calculators reproduce the `atmosphere`, `aerodynamics`, `orbital` and
  `rocketry` formulas implemented in the library.
- A data-service explorer builds the exact request each `nasa`, `esa`,
  `iss` and `isro` client method sends, shows the equivalent Python
  snippet, and can send the request live from the browser (services that
  block cross-origin requests can be opened in a new tab instead).
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

The website tests use Playwright and are skipped unless it is installed:

```bash
pip install playwright
playwright install chromium
pytest tests/test_website.py
```
