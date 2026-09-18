"""Connectivity to Indian Space Research Organisation (ISRO) data services.

This module provides a lightweight client, :class:`ISROClient`, for
connecting to public data services covering ISRO programs, missions and
spacecraft:

- **ISRO public API** — catalogues of ISRO spacecraft, launchers, customer
  satellites launched by ISRO, and ISRO centres, via
  https://isro.vercel.app/api/.
- **Launch Library 2** — ISRO launch records (past and upcoming) and agency
  metadata, via https://ll.thespacedevs.com/2.2.0/.
- **CelesTrak** — orbital elements for ISRO-operated spacecraft, including
  the NavIC (IRNSS) navigation constellation, via
  https://celestrak.org/NORAD/elements/gp.php.

All of these services offer read-only access without requiring an API key
or account, so :class:`ISROClient` needs no credentials.
"""

from __future__ import annotations

from typing import Any, Optional

import requests

#: Base URL for the public ISRO API (spacecraft, launchers, centres).
ISRO_API_BASE_URL = "https://isro.vercel.app/api"

#: Base URL for the Launch Library 2 API.
LAUNCH_LIBRARY_BASE_URL = "https://ll.thespacedevs.com/2.2.0"

#: Launch Library 2 agency identifier for ISRO.
ISRO_AGENCY_ID = 31

#: URL for the CelesTrak general perturbations (GP) orbital element service.
CELESTRAK_GP_URL = "https://celestrak.org/NORAD/elements/gp.php"

#: Default HTTP request timeout, in seconds.
DEFAULT_TIMEOUT = 30


class ISROAPIError(RuntimeError):
    """Raised when an ISRO data service request fails or errors out."""


class ISROClient:
    """Client providing connectivity to ISRO program data services.

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
            raise ISROAPIError(f"Request to {url} failed: {exc}") from exc
        if not response.ok:
            raise ISROAPIError(
                f"ISRO data service request to {url} failed with status "
                f"{response.status_code}: {response.text}"
            )
        return response.json()

    def _get_text(self, url: str, params: Optional[dict] = None) -> str:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ISROAPIError(f"Request to {url} failed: {exc}") from exc
        if not response.ok:
            raise ISROAPIError(
                f"ISRO data service request to {url} failed with status "
                f"{response.status_code}: {response.text}"
            )
        return response.text

    # -- ISRO public API ---------------------------------------------------

    def spacecrafts(self) -> Any:
        """Return the catalogue of ISRO spacecraft and satellites."""
        return self._get(f"{ISRO_API_BASE_URL}/spacecrafts")

    def launchers(self) -> Any:
        """Return the catalogue of ISRO launch vehicles (SLV, PSLV, GSLV...)."""
        return self._get(f"{ISRO_API_BASE_URL}/launchers")

    def customer_satellites(self) -> Any:
        """Return foreign customer satellites launched by ISRO."""
        return self._get(f"{ISRO_API_BASE_URL}/customer_satellites")

    def centres(self) -> Any:
        """Return ISRO centres and units with their locations."""
        return self._get(f"{ISRO_API_BASE_URL}/centres")

    # -- Launch Library 2 (ISRO launches) ----------------------------------

    def launches(
        self,
        upcoming: bool = False,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """Return ISRO launches from Launch Library 2.

        By default past launches are returned; set ``upcoming=True`` for
        scheduled launches. ``search`` filters by free text (for example a
        mission or vehicle name).
        """
        endpoint = "upcoming" if upcoming else "previous"
        params: dict = {"lsp__id": ISRO_AGENCY_ID}
        if search is not None:
            params["search"] = search
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        return self._get(f"{LAUNCH_LIBRARY_BASE_URL}/launch/{endpoint}/", params)

    def agency(self) -> Any:
        """Return Launch Library 2 agency metadata for ISRO."""
        return self._get(f"{LAUNCH_LIBRARY_BASE_URL}/agencies/{ISRO_AGENCY_ID}/")

    # -- CelesTrak ---------------------------------------------------------

    def celestrak_elements(
        self,
        norad_id: Optional[int] = None,
        group: Optional[str] = None,
        name: Optional[str] = None,
        fmt: str = "json",
    ) -> Any:
        """Return orbital elements for ISRO spacecraft from CelesTrak's GP service.

        Query a single object by ``norad_id``, a CelesTrak ``group`` (such as
        ``"gnss"``), or a ``name`` fragment (such as ``"IRNSS"``). When more
        than one is supplied, ``group`` takes precedence over ``norad_id``,
        which takes precedence over ``name``. ``fmt`` selects the CelesTrak
        format — ``"json"`` (parsed) or a text format such as ``"tle"`` or
        ``"csv"`` (returned as a string).
        """
        fmt = fmt.lower()
        params: dict = {"FORMAT": fmt}
        if group is not None:
            params["GROUP"] = group
        elif norad_id is not None:
            params["CATNR"] = norad_id
        elif name is not None:
            params["NAME"] = name
        else:
            raise ValueError("One of norad_id, group or name must be provided")
        if fmt in ("json", "json-pretty"):
            return self._get(CELESTRAK_GP_URL, params)
        return self._get_text(CELESTRAK_GP_URL, params)

    def navic_elements(self, fmt: str = "json") -> Any:
        """Return orbital elements for the NavIC (IRNSS) constellation."""
        return self.celestrak_elements(name="IRNSS", fmt=fmt)
