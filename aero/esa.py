"""Connectivity to European Space Agency (ESA) public data services.

This module provides a lightweight client, :class:`ESAClient`, for
connecting to a range of European space programs and public data services
operated by ESA and its partners:

- **ESA Open Data Portal** — dataset catalogue search and metadata lookup,
  via the CKAN Action API at https://data.esa.int/.
- **Copernicus Data Space Ecosystem** — search for Sentinel satellite
  products (Copernicus Programme), via the public OData API at
  https://catalogue.dataspace.copernicus.eu/.
- **Gaia Archive** — astrometric/photometric star catalogue queries via the
  TAP+/ADQL service at https://gea.esac.esa.int/.
- **NEOCC** — the Near-Earth Object Coordination Centre's risk list and
  orbital data, via the TAP/ADQL service at https://neo.ssa.esa.int/.

All of these services expose read access (catalogue search and metadata)
without requiring an API key or account, so :class:`ESAClient` needs no
credentials for the operations implemented here.
"""

from __future__ import annotations

from typing import Any, Optional

import requests

#: Base URL for the ESA Open Data Portal's CKAN Action API.
ESA_OPEN_DATA_BASE_URL = "https://data.esa.int/api/3/action"

#: Base URL for the Copernicus Data Space Ecosystem OData API.
COPERNICUS_ODATA_BASE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1"

#: Base URL for the Gaia Archive TAP+ synchronous query endpoint.
GAIA_TAP_SYNC_URL = "https://gea.esac.esa.int/tap-server/tap/sync"

#: Base URL for the ESA NEOCC TAP synchronous query endpoint.
NEOCC_TAP_SYNC_URL = "https://neo.ssa.esa.int/tap/sync"

#: Default HTTP request timeout, in seconds.
DEFAULT_TIMEOUT = 30


class ESAAPIError(RuntimeError):
    """Raised when an ESA data service request fails or errors out."""


class ESAClient:
    """Client providing connectivity to multiple European space programs.

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
            raise ESAAPIError(f"Request to {url} failed: {exc}") from exc
        if not response.ok:
            raise ESAAPIError(
                f"ESA data service request to {url} failed with status "
                f"{response.status_code}: {response.text}"
            )
        return response.json()

    # -- ESA Open Data Portal (CKAN) --------------------------------------

    def open_data_search(self, query: str = "", rows: Optional[int] = None) -> Any:
        """Search the ESA Open Data Portal dataset catalogue.

        ``query`` is a free-text CKAN search string (for example
        ``"satellite"``); an empty string returns all datasets.
        """
        params: dict = {"q": query}
        if rows is not None:
            params["rows"] = rows
        return self._get(f"{ESA_OPEN_DATA_BASE_URL}/package_search", params)

    def open_data_dataset(self, dataset_id: str) -> Any:
        """Return metadata for a specific ESA Open Data Portal dataset."""
        return self._get(
            f"{ESA_OPEN_DATA_BASE_URL}/package_show", {"id": dataset_id}
        )

    # -- Copernicus Data Space Ecosystem (Sentinel products) ---------------

    def copernicus_products(
        self,
        collection: Optional[str] = None,
        filter_: Optional[str] = None,
        top: Optional[int] = None,
        orderby: Optional[str] = None,
    ) -> Any:
        """Search Copernicus Sentinel satellite products.

        ``collection`` is a shorthand for filtering by mission (for example
        ``"SENTINEL-2"``) and is combined with ``filter_`` (a raw OData
        ``$filter`` expression) when both are given.
        """
        clauses = []
        if collection is not None:
            clauses.append(f"Collection/Name eq '{collection}'")
        if filter_ is not None:
            clauses.append(filter_)
        params: dict = {}
        if clauses:
            params["$filter"] = " and ".join(clauses)
        if top is not None:
            params["$top"] = top
        if orderby is not None:
            params["$orderby"] = orderby
        return self._get(f"{COPERNICUS_ODATA_BASE_URL}/Products", params)

    # -- Gaia Archive (star catalogue) -------------------------------------

    def gaia_query(
        self, query: str = "select top 10 * from gaiadr3.gaia_source", fmt: str = "json"
    ) -> Any:
        """Query the Gaia star catalogue archive using ADQL."""
        params = {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": fmt, "QUERY": query}
        return self._get(GAIA_TAP_SYNC_URL, params)

    # -- NEOCC (Near-Earth Object Coordination Centre) ---------------------

    def neocc_risk_list(
        self, query: str = "select * from neocc.risk", fmt: str = "json"
    ) -> Any:
        """Query the ESA NEOCC near-Earth object risk list using ADQL."""
        params = {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": fmt, "QUERY": query}
        return self._get(NEOCC_TAP_SYNC_URL, params)
