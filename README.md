# aero

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Website](https://img.shields.io/badge/website-charles2ke.github.io%2Faero-5cc8ff.svg)](https://charles2ke.github.io/aero/)
[![Deploy website to GitHub Pages](https://github.com/charles2ke/aero/actions/workflows/pages.yml/badge.svg)](https://github.com/charles2ke/aero/actions/workflows/pages.yml)

A small, dependency-light Python library of common aerospace engineering
calculations — standard atmosphere, aerodynamics, orbital mechanics,
rocketry and great-circle navigation — plus read-only clients for public
space-agency data services (NASA, ESA, ISS and ISRO).

**Website: <https://charles2ke.github.io/aero/>** — interactive calculators,
a live data explorer, a searchable API reference and the latest changes at
each data source. Press <kbd>Ctrl</kbd> <kbd>K</kbd> (<kbd>⌘</kbd>
<kbd>K</kbd> on a Mac) or <kbd>/</kbd> to search, or link straight to a
search such as <https://charles2ke.github.io/aero/?q=delta_v>.

The calculation helpers are pure Python with type hints and use SI units,
except that `aero.navigation` takes latitude, longitude and bearings in
degrees (and `central_angle` returns radians). The data-service clients
perform HTTP requests and return the provider's payload as-is, so their
values are in whatever units the service publishes. Everything is covered
by tests.

## Contents

- [What's new](#whats-new)
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

## What's new

The data-service clients were checked against each provider's own
documentation and source repositories on 12 November 2026.

- **NASA APOD moved.** NASA Science now serves the Astronomy Picture of the
  Day at `science.nasa.gov/wp-json/wp/v2/apod-basic` without an API key,
  and the legacy `api.nasa.gov/planetary/apod` service goes offline on
  1 December 2026. `NASAClient.apod()` uses the new service; `url` is now
  the APOD post page and `hdurl` the image.
- **Three new keyless calls:** `NASAClient.eonet_events()` (EONET v3
  natural events), `NASAClient.image_search()` (NASA Image and Video
  Library) and `ESAClient.neocc_query()` (ADQL on the NEOCC TAP server at
  `dachs.neo.s2p.esa.int`).
- **TechPort moved** to `techport.nasa.gov/api`. `techport_projects()` now
  requires `updated_since`, and an optional TechPort token can be passed as
  `techport_token=` or set in `TECHPORT_API_TOKEN`.
- **Retired and archival NASA feeds.** NASA retired the Mars Rover Photos
  API, so `mars_rover_photos()` is deprecated in favour of
  `image_search()`. The InSight weather feed was last updated in 2021.
- **ESA NEOCC.** `neocc_risk_list()` uses NEOCC's automated download
  service.
- **ESA Gaia.** Gaia DR3 stays the default until ESA publishes Gaia DR4 on
  2 December 2026.
- **ESA Data Discovery Portal.** `open_data_search()` and
  `open_data_dataset()` are deprecated: data.esa.int documents no CKAN API.
- **ISS.** Open Notify serves plain HTTP only and is no longer maintained,
  so `current_location()` and `people_in_space()` now use `http://`, and
  "Where the ISS at?" (`satellite_position()`) is the recommended HTTPS
  source. Prefer CelesTrak's default JSON (OMM) format: the NORAD catalogue
  passed 99,999 in July 2026, and CelesTrak's TLE output omits six-digit
  catalogue numbers.
- **ISRO.** Launch data now comes from Launch Library 2.3.0, which allows
  up to 15 anonymous calls per hour per IP address. The ISRO catalogue API
  is a community project whose data was last updated in January 2025.

## Installation

Python 3.8 or newer is required. The only runtime dependency is
[`requests`](https://pypi.org/project/requests/), used by the data-service
clients. Install straight from GitHub — the `aero` name on PyPI belongs to
an unrelated project:

```bash
pip install git+https://github.com/charles2ke/aero.git
```

Or work from a clone:

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
| `aero.nasa` | `NASAClient` | NASA Open APIs (NeoWs, DONKI, EPIC), APOD from NASA Science, EONET natural events, the NASA Image and Video Library, TechPort, the Exoplanet Archive and the archival InSight Mars weather feed. Mars Rover Photos is deprecated. |
| `aero.esa` | `ESAClient` | Copernicus Data Space Ecosystem (Sentinel products), Gaia Archive (DR3), NEOCC near-Earth object risk list and TAP service. The ESA Data Discovery Portal methods are deprecated. |
| `aero.iss` | `ISSClient` | "Where the ISS at?" (state vectors, propagated positions, TLEs), CelesTrak elements for the ISS and the `stations` group, and Open Notify (people in space, basic ISS position; HTTP only). |
| `aero.isro` | `ISROClient` | Community ISRO API (spacecraft, launchers, customer satellites, centres), ISRO launch records from Launch Library 2.3.0, CelesTrak elements for ISRO spacecraft including NavIC (IRNSS). |

Only the `api.nasa.gov` endpoints use an API key (TechPort optionally
takes a token); every other service is read-only and needs no account.

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
scripts/    maintenance scripts (the website's API reference generator)
tests/      pytest suite, with HTTP calls stubbed out
website/    static site: calculators, data explorer, API reference, search
```

## Connecting to NASA programs

`aero.nasa.NASAClient` provides connectivity to several NASA Open APIs.
Register a free API key at https://api.nasa.gov/ and set it via the
`NASA_API_KEY` environment variable (or pass `api_key=...` explicitly). If
no key is provided, NASA's rate-limited `DEMO_KEY` is used.

```python
from aero import nasa

client = nasa.NASAClient()  # uses NASA_API_KEY env var, or DEMO_KEY

client.apod()                                  # latest APOD (NASA Science, no key)
client.apod(start_date="2026-11-01")           # every entry from 1 Nov to today
client.neo_feed(start_date="2026-11-01", end_date="2026-11-07")
client.neo_lookup("2000433")                   # 433 Eros
client.donki_notifications(start_date="2026-11-01")
client.epic_natural_images()
client.eonet_events(limit=5)                   # EONET natural events, no key
client.image_search(query="Artemis", media_type="image")  # no key
client.techport_projects(updated_since="2026-01-01")
client.exoplanets(query="select pl_name from ps")  # no key
client.insight_weather()                       # archival: last updated in 2021
```

The API key is only sent to `api.nasa.gov`. `mars_rover_photos()` is
deprecated because NASA retired that API; use `image_search()` for rover
imagery instead.

## Connecting to European space programs

`aero.esa.ESAClient` provides connectivity to public European Space
Agency (ESA) data services. None of these read-only endpoints require an
API key or account.

```python
from aero import esa

client = esa.ESAClient()

client.copernicus_products(                           # Copernicus Sentinel products
    collection="SENTINEL-2", top=5, orderby="ContentDate/Start desc"
)
client.gaia_query("select top 10 * from gaiadr3.gaia_source")  # Gaia Archive (DR3)
client.neocc_risk_list()                              # NEOCC risk list (text)
client.neocc_query("SELECT table_name FROM TAP_SCHEMA.tables")  # NEOCC TAP
```

`open_data_search()` and `open_data_dataset()` still exist but are
deprecated: data.esa.int is a metadata and DOI landing-page portal with no
documented CKAN API.

## Connecting to International Space Station programs

`aero.iss.ISSClient` provides connectivity to public International Space
Station data services. None of these read-only endpoints require an API key
or account.

```python
from aero import iss

client = iss.ISSClient()

client.satellite_position()                  # Where the ISS at?: ISS state vector
client.satellite_positions([1436029892])     # Where the ISS at?: up to 10 timestamps
client.tle()                                 # Where the ISS at?: latest ISS TLE
client.celestrak_elements()                  # CelesTrak: ISS elements (JSON/OMM)
client.station_elements()                    # CelesTrak: all "stations" group objects
client.people_in_space()                     # Open Notify: crew currently in orbit
client.current_location()                    # Open Notify: ISS ground track point
```

Open Notify only serves plain HTTP, is no longer maintained and updates
its crew list by hand, so prefer `satellite_position()` for positions.

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

The ISRO catalogue endpoints come from
[isro/api](https://github.com/isro/api), a community project rather than an
official ISRO service. Launch Library 2 allows up to 15 anonymous calls per
hour per IP address.

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
    position = client.satellite_position()
except iss.ISSAPIError as exc:
    print(f"ISS service unavailable: {exc}")
```

## Website

The project website, <https://charles2ke.github.io/aero/>, is a static
site in [`website/`](website/) with no framework or third-party scripts:

- **Search** — press <kbd>Ctrl</kbd> <kbd>K</kbd> (<kbd>⌘</kbd>
  <kbd>K</kbd> on a Mac) or <kbd>/</kbd> to search every function,
  explorer endpoint, data-source update and section. Results jump straight
  to the matching entry. `?q=` links open a pre-filled search, for example
  <https://charles2ke.github.io/aero/?q=delta_v>.
- **Latest from the agencies** — a dated timeline of the data-source
  changes above, with countdowns to upcoming events such as Gaia DR4.
- **Calculators** reproduce the `atmosphere`, `aerodynamics`, `orbital`,
  `rocketry` and `navigation` formulas implemented in the library.
- **Data explorer** — builds the exact request each `nasa`, `esa`, `iss`
  and `isro` client method sends, shows the equivalent Python snippet, and
  can send the request live from the browser. Services that block
  cross-origin calls can be retried once through a public CORS proxy; the
  proxy is never offered when the request carries your own API key.
- **Sources & status** — every host each client calls, what it needs and
  what to watch for.
- **API reference** — every public function and client method, generated
  from the package's signatures and docstrings.
- One-click copy buttons on every code block, keyboard navigation, and
  animations that switch off for visitors who prefer reduced motion.

For search engines, the page ships a description, canonical URL, Open
Graph and Twitter cards, JSON-LD structured data (including a search
action), an [OpenSearch](website/opensearch.xml) description so browsers
can add the site as a search engine, and a [sitemap](website/sitemap.xml).
A project site cannot serve the domain's root `robots.txt`, so submit
`https://charles2ke.github.io/aero/sitemap.xml` in
[Google Search Console](https://search.google.com/search-console) and
[Bing Webmaster Tools](https://www.bing.com/webmasters) to get it indexed
sooner.

The API reference sits between markers in `website/index.html`. Regenerate
it after changing a public function or docstring:

```bash
python scripts/build_api_reference.py          # rewrite the reference
python scripts/build_api_reference.py --check  # exit 1 if it is stale
```

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

`tests/test_site_files.py` checks the sitemap, the OpenSearch description
and that the generated API reference matches the package. The website
tests use Playwright and are skipped unless it is installed:

```bash
pip install playwright
playwright install chromium
pytest tests/test_website.py
```

## License

Released under the [MIT License](LICENSE).
