"""Tests for aero.iss connectivity to International Space Station services.

All HTTP calls are mocked so the tests run offline and deterministically.
"""

from unittest.mock import MagicMock

import pytest
import requests

from aero import iss


def _mock_response(json_data=None, status_code=200, ok=True, text=""):
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.status_code = status_code
    resp.ok = ok
    resp.text = text
    return resp


def test_current_location():
    session = MagicMock()
    session.get.return_value = _mock_response({"message": "success"})
    client = iss.ISSClient(session=session)

    result = client.current_location()

    assert result == {"message": "success"}
    args, kwargs = session.get.call_args
    assert args[0] == f"{iss.OPEN_NOTIFY_BASE_URL}/iss-now.json"


def test_people_in_space():
    session = MagicMock()
    session.get.return_value = _mock_response({"number": 7})
    client = iss.ISSClient(session=session)

    result = client.people_in_space()

    assert result == {"number": 7}
    args, kwargs = session.get.call_args
    assert args[0] == f"{iss.OPEN_NOTIFY_BASE_URL}/astros.json"


def test_satellite_position_defaults_to_iss():
    session = MagicMock()
    session.get.return_value = _mock_response({"name": "iss"})
    client = iss.ISSClient(session=session)

    result = client.satellite_position()

    assert result == {"name": "iss"}
    args, kwargs = session.get.call_args
    assert args[0] == (
        f"{iss.WHERE_THE_ISS_AT_BASE_URL}/satellites/{iss.ISS_NORAD_ID}"
    )
    assert kwargs["params"] == {}


def test_satellite_position_with_units():
    session = MagicMock()
    session.get.return_value = _mock_response({"name": "iss"})
    client = iss.ISSClient(session=session)

    client.satellite_position(units="miles")

    args, kwargs = session.get.call_args
    assert kwargs["params"]["units"] == "miles"


def test_satellite_positions_joins_timestamps():
    session = MagicMock()
    session.get.return_value = _mock_response([{"name": "iss"}])
    client = iss.ISSClient(session=session)

    result = client.satellite_positions([1436029892, 1436029902])

    assert result == [{"name": "iss"}]
    args, kwargs = session.get.call_args
    assert args[0] == (
        f"{iss.WHERE_THE_ISS_AT_BASE_URL}/satellites/{iss.ISS_NORAD_ID}/positions"
    )
    assert kwargs["params"]["timestamps"] == "1436029892,1436029902"


def test_satellite_positions_requires_timestamps():
    client = iss.ISSClient(session=MagicMock())

    with pytest.raises(ValueError):
        client.satellite_positions([])


def test_satellite_positions_rejects_more_than_ten_timestamps():
    client = iss.ISSClient(session=MagicMock())

    with pytest.raises(ValueError):
        client.satellite_positions(range(11))


def test_tle():
    session = MagicMock()
    session.get.return_value = _mock_response({"line1": "1 25544U"})
    client = iss.ISSClient(session=session)

    result = client.tle()

    assert result == {"line1": "1 25544U"}
    args, kwargs = session.get.call_args
    assert args[0] == (
        f"{iss.WHERE_THE_ISS_AT_BASE_URL}/satellites/{iss.ISS_NORAD_ID}/tles"
    )


def test_celestrak_elements_by_catalog_number():
    session = MagicMock()
    session.get.return_value = _mock_response([{"OBJECT_NAME": "ISS (ZARYA)"}])
    client = iss.ISSClient(session=session)

    result = client.celestrak_elements()

    assert result == [{"OBJECT_NAME": "ISS (ZARYA)"}]
    args, kwargs = session.get.call_args
    assert args[0] == iss.CELESTRAK_GP_URL
    assert kwargs["params"]["CATNR"] == iss.ISS_NORAD_ID
    assert kwargs["params"]["FORMAT"] == "json"


def test_celestrak_elements_text_format_returns_text():
    session = MagicMock()
    session.get.return_value = _mock_response(text="ISS (ZARYA)\n1 25544U\n2 25544")
    client = iss.ISSClient(session=session)

    result = client.celestrak_elements(fmt="tle")

    assert result == "ISS (ZARYA)\n1 25544U\n2 25544"
    args, kwargs = session.get.call_args
    assert kwargs["params"]["FORMAT"] == "tle"


def test_celestrak_elements_requires_target():
    client = iss.ISSClient(session=MagicMock())

    with pytest.raises(ValueError):
        client.celestrak_elements(norad_id=None)


def test_station_elements_uses_group():
    session = MagicMock()
    session.get.return_value = _mock_response([{"OBJECT_NAME": "ISS (ZARYA)"}])
    client = iss.ISSClient(session=session)

    client.station_elements()

    args, kwargs = session.get.call_args
    assert kwargs["params"]["GROUP"] == "stations"
    assert "CATNR" not in kwargs["params"]


def test_error_response_raises():
    session = MagicMock()
    session.get.return_value = _mock_response(
        None, status_code=503, ok=False, text="Service Unavailable"
    )
    client = iss.ISSClient(session=session)

    with pytest.raises(iss.ISSAPIError):
        client.current_location()


def test_error_response_raises_for_text_endpoint():
    session = MagicMock()
    session.get.return_value = _mock_response(
        None, status_code=404, ok=False, text="Not Found"
    )
    client = iss.ISSClient(session=session)

    with pytest.raises(iss.ISSAPIError):
        client.celestrak_elements(fmt="tle")


def test_request_exception_raises_iss_error():
    session = MagicMock()
    session.get.side_effect = requests.ConnectionError("boom")
    client = iss.ISSClient(session=session)

    with pytest.raises(iss.ISSAPIError):
        client.satellite_position()
