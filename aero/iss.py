"""Connectivity to International Space Station (ISS) program data services.

This module provides a lightweight client, :class:`ISSClient`, for
connecting to public data services covering the International Space Station
program and its crewed operations:

- **Open Notify** — the current sub-satellite point of the ISS and the list
  of people currently in space, via https://api.open-notify.org/.
- **Where the ISS at?** — ISS state vectors (position, velocity, altitude,
  visibility), historical/predicted positions for given timestamps, and the
  latest two-line element (TLE) set, via https://api.wheretheiss.at/.
- **CelesTrak** — orbital elements for the ISS and the other objects in the
  ``stations`` group (Tiangong, ISS visiting vehicles, deployed cubesats),
  via https://celestrak.org/NORAD/elements/gp.php.

All of these services offer read-only access without requiring an API key
or account, so :class:`ISSClient` needs no credentials.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional, Union

import requests

#: NORAD catalogue number of the International Space Station (ZARYA).
ISS_NORAD_ID = 25544

#: Base URL for the Open Notify ISS API.
OPEN_NOTIFY_BASE_URL = "https://api.open-notify.org"

#: Base URL for the "Where the ISS at?" API.
WHERE_THE_ISS_AT_BASE_URL = "https://api.wheretheiss.at/v1"

#: URL for the CelesTrak general perturbations (GP) orbital element service.
CELESTRAK_GP_URL = "https://celestrak.org/NORAD/elements/gp.php"

#: Default HTTP request timeout, in seconds.
DEFAULT_TIMEOUT = 30


class ISSAPIError(RuntimeError):
    """Raised when an ISS data service request fails or errors out."""


class ISSClient:
    """Client providing connectivity to International Space Station services.

    Parameters
    ----------
    session:
        Optional :class:`requests.Session` to use for HTTP requests. A new
        session is created if not provided.
    timeout:
        Request timeout, in seconds.
    """

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout

    # -- internal helpers -------------------------------------------------

    def _get(self, url: str, params: Optional[dict] = None) -> Any:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ISSAPIError(f"Request to {url} failed: {exc}") from exc
        if not response.ok:
            raise ISSAPIError(
                f"ISS data service request to {url} failed with status "
                f"{response.status_code}: {response.text}"
            )
        return response.json()

    def _get_text(self, url: str, params: Optional[dict] = None) -> str:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ISSAPIError(f"Request to {url} failed: {exc}") from exc
        if not response.ok:
            raise ISSAPIError(
                f"ISS data service request to {url} failed with status "
                f"{response.status_code}: {response.text}"
            )
        return response.text

    # -- Open Notify -------------------------------------------------------

    def current_location(self) -> Any:
        """Return the ISS's current latitude/longitude from Open Notify."""
        return self._get(f"{OPEN_NOTIFY_BASE_URL}/iss-now.json")

    def people_in_space(self) -> Any:
        """Return the people currently in space and their spacecraft.

        This covers the ISS expedition crew alongside any other crewed
        vehicles or stations in orbit at the time of the request.
        """
        return self._get(f"{OPEN_NOTIFY_BASE_URL}/astros.json")

    # -- Where the ISS at? -------------------------------------------------

    def satellite_position(
        self, norad_id: int = ISS_NORAD_ID, units: Optional[str] = None
    ) -> Any:
        """Return the current state vector for a tracked satellite.

        Defaults to the ISS. ``units`` may be ``"kilometers"`` (default of
        the service) or ``"miles"``.
        """
        params: dict = {}
        if units is not None:
            params["units"] = units
        return self._get(
            f"{WHERE_THE_ISS_AT_BASE_URL}/satellites/{norad_id}", params
        )

    def satellite_positions(
        self,
        timestamps: Iterable[Union[int, str]],
        norad_id: int = ISS_NORAD_ID,
        units: Optional[str] = None,
    ) -> Any:
        """Return state vectors for up to 10 Unix ``timestamps``.

        Timestamps may be in the past or the future; the service propagates
        the orbit from the latest available element set.
        """
        stamps = [str(stamp) for stamp in timestamps]
        if not stamps:
            raise ValueError("At least one timestamp is required")
        if len(stamps) > 10:
            raise ValueError("At most 10 timestamps are allowed")
        params: dict = {"timestamps": ",".join(stamps)}
        if units is not None:
            params["units"] = units
        return self._get(
            f"{WHERE_THE_ISS_AT_BASE_URL}/satellites/{norad_id}/positions", params
        )

    def tle(self, norad_id: int = ISS_NORAD_ID) -> Any:
        """Return the latest two-line element set for a tracked satellite."""
        return self._get(f"{WHERE_THE_ISS_AT_BASE_URL}/satellites/{norad_id}/tles")

    # -- CelesTrak ---------------------------------------------------------

    def celestrak_elements(
        self,
        norad_id: Optional[int] = ISS_NORAD_ID,
        group: Optional[str] = None,
        fmt: str = "json",
    ) -> Any:
        """Return orbital elements from CelesTrak's GP service.

        Query either a single object by ``norad_id`` (the ISS by default) or
        a whole ``group`` such as ``"stations"``; when ``group`` is given it
        takes precedence. ``fmt`` selects the CelesTrak format — ``"json"``
        (parsed) or a text format such as ``"tle"`` or ``"csv"`` (returned
        as a string).
        """
        params: dict = {"FORMAT": fmt}
        if group is not None:
            params["GROUP"] = group
        elif norad_id is not None:
            params["CATNR"] = norad_id
        else:
            raise ValueError("Either norad_id or group must be provided")
        if fmt.lower() in ("json", "json-pretty"):
            return self._get(CELESTRAK_GP_URL, params)
        return self._get_text(CELESTRAK_GP_URL, params)

    def station_elements(self, fmt: str = "json") -> Any:
        """Return orbital elements for CelesTrak's ``stations`` group.

        The group covers the ISS, its visiting vehicles and deployed
        payloads, and other crewed stations such as Tiangong.
        """
        return self.celestrak_elements(norad_id=None, group="stations", fmt=fmt)
