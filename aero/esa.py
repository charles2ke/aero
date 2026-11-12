"""Connectivity to European Space Agency (ESA) public data services.

This module provides a lightweight client, :class:`ESAClient`, for
connecting to a range of European space programs and public data services
operated by ESA and its partners:

- **Copernicus Data Space Ecosystem** — search for Sentinel satellite
  products (Copernicus Programme), via the public OData API at
  https://catalogue.dataspace.copernicus.eu/.
- **Gaia Archive** — astrometric/photometric star catalogue queries via the
  TAP+/ADQL service at https://gea.esac.esa.int/. Data Release 3 is the
  current release; ESA has scheduled Gaia DR4 for 2 December 2026.
- **NEOCC** — the Near-Earth Object Coordination Centre's daily risk list,
  via its automated data access service at https://neo.ssa.esa.int/, and
  ADQL queries via the NEOCC TAP server at https://dachs.neo.s2p.esa.int/.
- **ESA Data Discovery Portal** — *deprecated*: https://data.esa.int/ is a
  metadata and DOI landing-page portal with no documented CKAN Action API,
  so :meth:`ESAClient.open_data_search` and
  :meth:`ESAClient.open_data_dataset` will be removed.

All of these services expose read access (catalogue search and metadata)
without requiring an API key or account, so :class:`ESAClient` needs no
credentials for the operations implemented here.
"""

from __future__ import annotations

import warnings
from typing import Any, Optional

import requests

#: Deprecated: CKAN-style URL formerly used for https://data.esa.int/.
ESA_OPEN_DATA_BASE_URL = "https://data.esa.int/api/3/action"

#: Base URL for the Copernicus Data Space Ecosystem OData API.
COPERNICUS_ODATA_BASE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1"

#: Base URL for the Gaia Archive TAP+ synchronous query endpoint.
GAIA_TAP_SYNC_URL = "https://gea.esac.esa.int/tap-server/tap/sync"

#: ESA NEOCC automated data access (file download) endpoint.
NEOCC_DOWNLOAD_URL = "https://neo.ssa.esa.int/PSDB-portlet/download"

#: ESA NEOCC TAP server synchronous ADQL query endpoint.
NEOCC_TAP_SYNC_URL = "https://dachs.neo.s2p.esa.int/tap/sync"

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

    def _send(self, url: str, params: Optional[dict] = None) -> requests.Response:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ESAAPIError(f"Request to {url} failed: {exc}") from exc
        if not response.ok:
            raise ESAAPIError(
                f"ESA data service request to {url} failed with status "
                f"{response.status_code}: {response.text}"
            )
        return response

    def _get(self, url: str, params: Optional[dict] = None) -> Any:
        return self._send(url, params).json()

    def _get_text(self, url: str, params: Optional[dict] = None) -> str:
        return self._send(url, params).text

    # -- ESA Data Discovery Portal (deprecated) ---------------------------

    def open_data_search(self, query: str = "", rows: Optional[int] = None) -> Any:
        """Search data.esa.int with a CKAN-style ``package_search`` request.

        .. deprecated::
            data.esa.int is ESA's Data Discovery Portal, a metadata and DOI
            landing-page site with no documented CKAN Action API. Use the
            Copernicus, Gaia or NEOCC methods instead.
        """
        _warn_open_data_deprecated("open_data_search")
        params: dict = {"q": query}
        if rows is not None:
            params["rows"] = rows
        return self._get(f"{ESA_OPEN_DATA_BASE_URL}/package_search", params)

    def open_data_dataset(self, dataset_id: str) -> Any:
        """Fetch data.esa.int metadata with a CKAN-style ``package_show`` request.

        .. deprecated::
            See :meth:`open_data_search`.
        """
        _warn_open_data_deprecated("open_data_dataset")
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
        """Query the Gaia star catalogue archive using ADQL.

        The default query reads Gaia Data Release 3 (``gaiadr3``), the
        current release until Gaia DR4 is published on 2 December 2026.
        """
        params = {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": fmt, "QUERY": query}
        return self._get(GAIA_TAP_SYNC_URL, params)

    # -- NEOCC (Near-Earth Object Coordination Centre) ---------------------

    def neocc_risk_list(self) -> str:
        """Return ESA NEOCC's current near-Earth object risk list.

        The list is refreshed daily and returned as NEOCC publishes it:
        pipe-delimited plain text with a ``Last Update`` line and column
        headers, one row per object with a non-zero impact probability.
        """
        return self._get_text(NEOCC_DOWNLOAD_URL, {"file": "esa_risk_list"})

    def neocc_query(self, query: str, fmt: str = "json") -> Any:
        """Run an ADQL query on the ESA NEOCC TAP server.

        For example, ``"SELECT table_name, description FROM TAP_SCHEMA.tables"``
        lists the available tables. ``fmt="json"`` results are parsed; other
        formats such as ``"csv"`` or ``"votable"`` are returned as text.
        """
        fmt = fmt.lower()
        params = {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": fmt, "QUERY": query}
        if fmt == "json":
            return self._get(NEOCC_TAP_SYNC_URL, params)
        return self._get_text(NEOCC_TAP_SYNC_URL, params)


def _warn_open_data_deprecated(method: str) -> None:
    warnings.warn(
        f"{method}() is deprecated and will be removed: data.esa.int (ESA's "
        "Data Discovery Portal) has no documented CKAN Action API.",
        DeprecationWarning,
        stacklevel=3,
    )
