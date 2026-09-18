"""Connectivity to NASA's public Open APIs.

This module provides a lightweight client, :class:`NASAClient`, for
connecting to a range of NASA programs exposed through the
`api.nasa.gov <https://api.nasa.gov/>`_ Open APIs portal, as well as
NASA's public Exoplanet Archive.

Supported programs:

- **APOD** — Astronomy Picture of the Day
- **Mars Rover Photos** — Curiosity, Opportunity, Spirit, and Perseverance
- **NeoWs** — Near Earth Object Web Service (asteroid tracking)
- **DONKI** — Space Weather Database Of Notifications, Knowledge, Information
- **EPIC** — Earth Polychromatic Imaging Camera
- **InSight** — Mars weather (InSight lander, deprecated by NASA but still
  reachable through the same API surface)
- **TechPort** — NASA technology project portfolio
- **Exoplanet Archive** — confirmed exoplanet data (no API key required)

An API key is required for most ``api.nasa.gov`` endpoints. Register a free
key at https://api.nasa.gov/ and either pass it explicitly to
:class:`NASAClient` or set the ``NASA_API_KEY`` environment variable. When
neither is provided, NASA's shared ``DEMO_KEY`` is used, which is rate
limited and intended for evaluation only.
"""

from __future__ import annotations

import os
from typing import Any, Optional

import requests

#: Base URL for the api.nasa.gov Open APIs portal.
NASA_API_BASE_URL = "https://api.nasa.gov"

#: Base URL for NASA's public Exoplanet Archive TAP service.
EXOPLANET_ARCHIVE_BASE_URL = (
    "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
)

#: Fallback API key shared by NASA for evaluation purposes. Subject to
#: tighter rate limits than a personal key registered at api.nasa.gov.
DEMO_KEY = "DEMO_KEY"

#: Default HTTP request timeout, in seconds.
DEFAULT_TIMEOUT = 30


class NASAAPIError(RuntimeError):
    """Raised when a NASA API request fails or returns an error response."""


class NASAClient:
    """Client providing connectivity to multiple NASA programs.

    Parameters
    ----------
    api_key:
        API key for ``api.nasa.gov``. If omitted, the ``NASA_API_KEY``
        environment variable is used, falling back to :data:`DEMO_KEY`.
    session:
        Optional :class:`requests.Session` to use for HTTP requests. A new
        session is created if not provided.
    timeout:
        Request timeout, in seconds.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.api_key = api_key or os.environ.get("NASA_API_KEY", DEMO_KEY)
        self.session = session or requests.Session()
        self.timeout = timeout

    # -- internal helpers -------------------------------------------------

    def _get(self, url: str, params: Optional[dict] = None) -> Any:
        params = dict(params or {})
        params.setdefault("api_key", self.api_key)
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise NASAAPIError(f"Request to {url} failed: {exc}") from exc
        if not response.ok:
            raise NASAAPIError(
                f"NASA API request to {url} failed with status "
                f"{response.status_code}: {response.text}"
            )
        return response.json()

    # -- APOD ---------------------------------------------------------

    def apod(self, date: Optional[str] = None, **params: Any) -> Any:
        """Return the Astronomy Picture of the Day.

        ``date`` is an optional ``YYYY-MM-DD`` string. Additional keyword
        arguments are passed through as query parameters (for example
        ``start_date``, ``end_date``, or ``count``).
        """
        if date is not None:
            params["date"] = date
        return self._get(f"{NASA_API_BASE_URL}/planetary/apod", params)

    # -- Mars Rover Photos ---------------------------------------------

    def mars_rover_photos(
        self,
        rover: str = "curiosity",
        sol: Optional[int] = None,
        earth_date: Optional[str] = None,
        camera: Optional[str] = None,
        page: Optional[int] = None,
    ) -> Any:
        """Return Mars Rover photos for the given rover and sol/earth_date."""
        params: dict = {}
        if sol is not None:
            params["sol"] = sol
        if earth_date is not None:
            params["earth_date"] = earth_date
        if camera is not None:
            params["camera"] = camera
        if page is not None:
            params["page"] = page
        url = f"{NASA_API_BASE_URL}/mars-photos/api/v1/rovers/{rover}/photos"
        return self._get(url, params)

    # -- NeoWs (Near Earth Object Web Service) -------------------------

    def neo_feed(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> Any:
        """Return near-Earth objects within the given date range (max 7 days)."""
        params = {}
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date
        return self._get(f"{NASA_API_BASE_URL}/neo/rest/v1/feed", params)

    def neo_lookup(self, asteroid_id: str) -> Any:
        """Return details for a specific near-Earth object by its NASA JPL ID."""
        return self._get(f"{NASA_API_BASE_URL}/neo/rest/v1/neo/{asteroid_id}")

    # -- DONKI (space weather) -----------------------------------------

    def donki_notifications(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        notification_type: str = "all",
    ) -> Any:
        """Return DONKI space weather notifications."""
        params: dict = {"type": notification_type}
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date
        return self._get(f"{NASA_API_BASE_URL}/DONKI/notifications", params)

    # -- EPIC (Earth Polychromatic Imaging Camera) ---------------------

    def epic_natural_images(self, date: Optional[str] = None) -> Any:
        """Return EPIC natural-color Earth images, optionally for a date."""
        url = f"{NASA_API_BASE_URL}/EPIC/api/natural"
        if date is not None:
            url += f"/date/{date}"
        return self._get(url)

    # -- InSight Mars weather -------------------------------------------

    def insight_weather(self) -> Any:
        """Return the latest InSight Mars weather report."""
        params = {"feedtype": "json", "ver": "1.0"}
        return self._get(f"{NASA_API_BASE_URL}/insight_weather/", params)

    # -- TechPort (technology project portfolio) -----------------------

    def techport_projects(self, updated_since: Optional[str] = None) -> Any:
        """Return the list of NASA TechPort project IDs."""
        params = {}
        if updated_since is not None:
            params["updatedSince"] = updated_since
        return self._get(f"{NASA_API_BASE_URL}/techport/api/projects", params)

    def techport_project(self, project_id: int) -> Any:
        """Return details for a specific NASA TechPort project."""
        return self._get(f"{NASA_API_BASE_URL}/techport/api/projects/{project_id}")

    # -- Exoplanet Archive (no API key required) ------------------------

    def exoplanets(self, query: str = "select * from ps", fmt: str = "json") -> Any:
        """Query NASA's Exoplanet Archive using the TAP ADQL/SQL-like syntax."""
        params = {"query": query, "format": fmt}
        try:
            response = self.session.get(
                EXOPLANET_ARCHIVE_BASE_URL, params=params, timeout=self.timeout
            )
        except requests.RequestException as exc:
            raise NASAAPIError(
                f"Request to {EXOPLANET_ARCHIVE_BASE_URL} failed: {exc}"
            ) from exc
        if not response.ok:
            raise NASAAPIError(
                f"Exoplanet Archive request failed with status "
                f"{response.status_code}: {response.text}"
            )
        return response.json()
