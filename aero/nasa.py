"""Connectivity to NASA's public Open APIs.

This module provides a lightweight client, :class:`NASAClient`, for
connecting to a range of NASA programs listed on the
`api.nasa.gov <https://api.nasa.gov/>`_ Open APIs portal, as well as
NASA's public Exoplanet Archive.

Supported programs:

- **APOD** — Astronomy Picture of the Day, served by NASA Science at
  https://science.nasa.gov/wp-json/wp/v2/apod-basic (no API key). NASA
  migrated APOD there in September 2026 and takes the legacy
  ``api.nasa.gov/planetary/apod`` service offline on 1 December 2026.
- **NeoWs** — Near Earth Object Web Service (asteroid tracking)
- **DONKI** — Space Weather Database Of Notifications, Knowledge, Information
- **EPIC** — Earth Polychromatic Imaging Camera
- **EONET** — Earth Observatory Natural Event Tracker (no API key)
- **NASA Image and Video Library** — search images.nasa.gov (no API key)
- **TechPort** — NASA technology project portfolio, via
  https://techport.nasa.gov/api
- **Exoplanet Archive** — confirmed exoplanet data (no API key required)
- **InSight** — Mars weather; an archival feed that NASA last updated in
  2021 (the InSight mission ended in December 2022)
- **Mars Rover Photos** — *deprecated*: the service has been retired and is
  no longer listed on api.nasa.gov

An API key is required for the ``api.nasa.gov`` endpoints. Register a free
key at https://api.nasa.gov/ and either pass it explicitly to
:class:`NASAClient` or set the ``NASA_API_KEY`` environment variable. When
neither is provided, NASA's shared ``DEMO_KEY`` is used, which is rate
limited and intended for evaluation only. The key is only sent to
``api.nasa.gov``.
"""

from __future__ import annotations

import datetime as _dt
import os
import warnings
from typing import Any, Optional, Union

import requests

#: Base URL for the api.nasa.gov Open APIs portal.
NASA_API_BASE_URL = "https://api.nasa.gov"

#: URL for NASA Science's Astronomy Picture of the Day (APOD) API.
NASA_APOD_API_URL = "https://science.nasa.gov/wp-json/wp/v2/apod-basic"

#: Base URL for the NASA Image and Video Library API (images.nasa.gov).
NASA_IMAGE_LIBRARY_BASE_URL = "https://images-api.nasa.gov"

#: Base URL for the Earth Observatory Natural Event Tracker (EONET) v3 API.
EONET_BASE_URL = "https://eonet.gsfc.nasa.gov/api/v3"

#: Base URL for the NASA TechPort technology portfolio API.
TECHPORT_API_BASE_URL = "https://techport.nasa.gov/api"

#: Base URL for NASA's public Exoplanet Archive TAP service.
EXOPLANET_ARCHIVE_BASE_URL = (
    "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
)

#: Fallback API key shared by NASA for evaluation purposes. Subject to
#: tighter rate limits than a personal key registered at api.nasa.gov.
DEMO_KEY = "DEMO_KEY"

#: Default HTTP request timeout, in seconds.
DEFAULT_TIMEOUT = 30

DateLike = Union[str, _dt.date]


class NASAAPIError(RuntimeError):
    """Raised when a NASA API request fails or returns an error response."""


def _apod_date_code(value: DateLike) -> str:
    """Convert a ``YYYY-MM-DD`` string or date to APOD's ``YYMMDD`` code."""
    if isinstance(value, _dt.date):
        day = value
    else:
        try:
            day = _dt.date.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError(
                f"APOD dates must be YYYY-MM-DD strings or dates, got {value!r}"
            ) from exc
    return day.strftime("%y%m%d")


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
    techport_token:
        Optional TechPort API token, sent as an ``Authorization: Bearer``
        header to techport.nasa.gov. If omitted, the ``TECHPORT_API_TOKEN``
        environment variable is used when set.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
        timeout: float = DEFAULT_TIMEOUT,
        techport_token: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("NASA_API_KEY", DEMO_KEY)
        self.session = session or requests.Session()
        self.timeout = timeout
        self.techport_token = techport_token or os.environ.get("TECHPORT_API_TOKEN")

    # -- internal helpers -------------------------------------------------

    def _request(
        self,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> Any:
        kwargs: dict = {"params": params, "timeout": self.timeout}
        if headers:
            kwargs["headers"] = headers
        try:
            response = self.session.get(url, **kwargs)
        except requests.RequestException as exc:
            raise NASAAPIError(f"Request to {url} failed: {exc}") from exc
        if not response.ok:
            raise NASAAPIError(
                f"NASA API request to {url} failed with status "
                f"{response.status_code}: {response.text}"
            )
        return response.json()

    def _get(self, url: str, params: Optional[dict] = None) -> Any:
        """GET an ``api.nasa.gov`` endpoint, adding the API key."""
        params = dict(params or {})
        params.setdefault("api_key", self.api_key)
        return self._request(url, params)

    # -- APOD (science.nasa.gov, no API key) ------------------------------

    def apod(
        self,
        date: Optional[DateLike] = None,
        start_date: Optional[DateLike] = None,
        end_date: Optional[DateLike] = None,
    ) -> Any:
        """Return Astronomy Picture of the Day entries from NASA Science.

        With no arguments the most recently published entry is returned as
        a dict. ``date`` returns the entry for one day (a dict), while
        ``start_date`` and ``end_date`` return a list of entries for an
        inclusive range. Dates may be :class:`datetime.date` objects or
        ``YYYY-MM-DD`` strings; ``end_date`` defaults to today.

        Entries include ``title``, ``date``, ``explanation``, ``media_type``
        and ``hdurl`` (the image). Unlike the legacy api.nasa.gov service,
        ``url`` is the APOD post page rather than the image.
        """
        if date is not None and (start_date is not None or end_date is not None):
            raise ValueError("Pass either date or start_date/end_date, not both")
        if end_date is not None and start_date is None:
            raise ValueError("end_date requires start_date")

        if date is not None:
            return self._request(f"{NASA_APOD_API_URL}/{_apod_date_code(date)}")

        if start_date is not None:
            params = {
                "date_from": _apod_date_code(start_date),
                "date_to": _apod_date_code(
                    end_date if end_date is not None else _dt.date.today()
                ),
            }
            return self._request(NASA_APOD_API_URL, params)

        entries = self._request(NASA_APOD_API_URL, {"page": 1, "per_page": 1})
        if isinstance(entries, list):
            if not entries:
                raise NASAAPIError("The APOD service returned no entries")
            return entries[0]
        return entries

    # -- Mars Rover Photos (retired) ------------------------------------

    def mars_rover_photos(
        self,
        rover: str = "curiosity",
        sol: Optional[int] = None,
        earth_date: Optional[str] = None,
        camera: Optional[str] = None,
        page: Optional[int] = None,
    ) -> Any:
        """Return Mars Rover photos for the given rover and sol/earth_date.

        .. deprecated::
            NASA has retired the Mars Rover Photos API and removed it from
            api.nasa.gov. Use :meth:`image_search` to find rover imagery in
            the NASA Image and Video Library instead.
        """
        warnings.warn(
            "The Mars Rover Photos API has been retired and is no longer "
            "listed on api.nasa.gov; mars_rover_photos() will be removed in a "
            "future release. Use image_search() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
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

    # -- EONET (natural events, no API key) ----------------------------

    def eonet_events(
        self,
        status: str = "open",
        limit: Optional[int] = None,
        days: Optional[int] = None,
        category: Optional[str] = None,
    ) -> Any:
        """Return natural events (wildfires, storms, volcanoes...) from EONET.

        ``status`` is ``"open"`` (default), ``"closed"`` or ``"all"``;
        ``days`` limits results to events from the last N days and
        ``category`` filters by an EONET category ID such as
        ``"wildfires"`` or ``"severeStorms"``.
        """
        params: dict = {"status": status}
        if limit is not None:
            params["limit"] = limit
        if days is not None:
            params["days"] = days
        if category is not None:
            params["category"] = category
        return self._request(f"{EONET_BASE_URL}/events", params)

    # -- NASA Image and Video Library (no API key) ---------------------

    def image_search(
        self,
        query: Optional[str] = None,
        media_type: Optional[str] = None,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Any:
        """Search the NASA Image and Video Library (images.nasa.gov).

        ``query`` is free text such as ``"perseverance rover"``;
        ``media_type`` may be ``"image"``, ``"video"`` or ``"audio"`` (or a
        comma-separated combination).
        """
        params: dict = {}
        if query is not None:
            params["q"] = query
        if media_type is not None:
            params["media_type"] = media_type
        if year_start is not None:
            params["year_start"] = year_start
        if year_end is not None:
            params["year_end"] = year_end
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size
        if not params:
            raise ValueError("At least one search parameter is required")
        return self._request(f"{NASA_IMAGE_LIBRARY_BASE_URL}/search", params)

    # -- InSight Mars weather (archival) --------------------------------

    def insight_weather(self) -> Any:
        """Return the InSight Mars weather feed.

        This is an archival feed: NASA last updated it in 2021, it has
        significant gaps, and the InSight mission ended in December 2022.
        """
        params = {"feedtype": "json", "ver": "1.0"}
        return self._get(f"{NASA_API_BASE_URL}/insight_weather/", params)

    # -- TechPort (technology project portfolio) -----------------------

    def _techport_get(self, path: str, params: Optional[dict] = None) -> Any:
        headers = {"Accept": "application/json"}
        if self.techport_token:
            headers["Authorization"] = f"Bearer {self.techport_token}"
        return self._request(f"{TECHPORT_API_BASE_URL}{path}", params, headers)

    def techport_projects(self, updated_since: str) -> Any:
        """Return IDs of TechPort projects updated since a date.

        ``updated_since`` is an ISO-8601 date such as ``"2024-01-01"``;
        TechPort requires it for project listings.
        """
        return self._techport_get("/projects", {"updatedSince": updated_since})

    def techport_project(self, project_id: int) -> Any:
        """Return details for a specific NASA TechPort project."""
        return self._techport_get(f"/projects/{project_id}")

    # -- Exoplanet Archive (no API key required) ------------------------

    def exoplanets(self, query: str = "select * from ps", fmt: str = "json") -> Any:
        """Query NASA's Exoplanet Archive using the TAP ADQL/SQL-like syntax."""
        params = {"query": query, "format": fmt}
        return self._request(EXOPLANET_ARCHIVE_BASE_URL, params)
