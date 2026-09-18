"""Tests for aero.esa connectivity to European space program services.

All HTTP calls are mocked so the tests run offline and deterministically.
"""

from unittest.mock import MagicMock

import pytest
import requests

from aero import esa


def _mock_response(json_data, status_code=200, ok=True, text=""):
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.status_code = status_code
    resp.ok = ok
    resp.text = text
    return resp


def test_open_data_search():
    session = MagicMock()
    session.get.return_value = _mock_response({"result": {"count": 1}})
    client = esa.ESAClient(session=session)

    result = client.open_data_search(query="satellite", rows=5)

    assert result == {"result": {"count": 1}}
    args, kwargs = session.get.call_args
    assert args[0] == f"{esa.ESA_OPEN_DATA_BASE_URL}/package_search"
    assert kwargs["params"]["q"] == "satellite"
    assert kwargs["params"]["rows"] == 5


def test_open_data_dataset():
    session = MagicMock()
    session.get.return_value = _mock_response({"result": {"id": "abc"}})
    client = esa.ESAClient(session=session)

    result = client.open_data_dataset("abc")

    assert result == {"result": {"id": "abc"}}
    args, kwargs = session.get.call_args
    assert args[0] == f"{esa.ESA_OPEN_DATA_BASE_URL}/package_show"
    assert kwargs["params"]["id"] == "abc"


def test_copernicus_products_with_collection():
    session = MagicMock()
    session.get.return_value = _mock_response({"value": []})
    client = esa.ESAClient(session=session)

    result = client.copernicus_products(collection="SENTINEL-2", top=50)

    assert result == {"value": []}
    args, kwargs = session.get.call_args
    assert args[0] == f"{esa.COPERNICUS_ODATA_BASE_URL}/Products"
    assert kwargs["params"]["$filter"] == "Collection/Name eq 'SENTINEL-2'"
    assert kwargs["params"]["$top"] == 50


def test_copernicus_products_combines_filters():
    session = MagicMock()
    session.get.return_value = _mock_response({"value": []})
    client = esa.ESAClient(session=session)

    client.copernicus_products(
        collection="SENTINEL-2", filter_="CloudCover lt 30", orderby="ContentDate/Start"
    )

    args, kwargs = session.get.call_args
    assert kwargs["params"]["$filter"] == (
        "Collection/Name eq 'SENTINEL-2' and CloudCover lt 30"
    )
    assert kwargs["params"]["$orderby"] == "ContentDate/Start"


def test_copernicus_products_no_filters():
    session = MagicMock()
    session.get.return_value = _mock_response({"value": []})
    client = esa.ESAClient(session=session)

    client.copernicus_products()

    args, kwargs = session.get.call_args
    assert "$filter" not in kwargs["params"]


def test_gaia_query():
    session = MagicMock()
    session.get.return_value = _mock_response({"data": []})
    client = esa.ESAClient(session=session)

    result = client.gaia_query(query="select top 5 * from gaiadr3.gaia_source")

    assert result == {"data": []}
    args, kwargs = session.get.call_args
    assert args[0] == esa.GAIA_TAP_SYNC_URL
    assert kwargs["params"]["QUERY"] == "select top 5 * from gaiadr3.gaia_source"
    assert kwargs["params"]["LANG"] == "ADQL"


def test_neocc_risk_list():
    session = MagicMock()
    session.get.return_value = _mock_response({"data": []})
    client = esa.ESAClient(session=session)

    result = client.neocc_risk_list()

    assert result == {"data": []}
    args, kwargs = session.get.call_args
    assert args[0] == esa.NEOCC_TAP_SYNC_URL
    assert kwargs["params"]["QUERY"] == "select * from neocc.risk"


def test_error_response_raises():
    session = MagicMock()
    session.get.return_value = _mock_response(
        None, status_code=500, ok=False, text="Internal Server Error"
    )
    client = esa.ESAClient(session=session)

    with pytest.raises(esa.ESAAPIError):
        client.open_data_search()


def test_request_exception_raises_esa_error():
    session = MagicMock()
    session.get.side_effect = requests.ConnectionError("boom")
    client = esa.ESAClient(session=session)

    with pytest.raises(esa.ESAAPIError):
        client.gaia_query()
