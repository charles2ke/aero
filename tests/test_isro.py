"""Tests for aero.isro connectivity to ISRO program data services.

All HTTP calls are mocked so the tests run offline and deterministically.
"""

from unittest.mock import MagicMock

import pytest
import requests

from aero import isro


def _mock_response(json_data=None, status_code=200, ok=True, text=""):
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.status_code = status_code
    resp.ok = ok
    resp.text = text
    return resp


def test_spacecrafts():
    session = MagicMock()
    session.get.return_value = _mock_response({"spacecrafts": []})
    client = isro.ISROClient(session=session)

    result = client.spacecrafts()

    assert result == {"spacecrafts": []}
    args, kwargs = session.get.call_args
    assert args[0] == f"{isro.ISRO_API_BASE_URL}/spacecrafts"


def test_launchers():
    session = MagicMock()
    session.get.return_value = _mock_response({"launchers": []})
    client = isro.ISROClient(session=session)

    assert client.launchers() == {"launchers": []}
    args, _ = session.get.call_args
    assert args[0] == f"{isro.ISRO_API_BASE_URL}/launchers"


def test_customer_satellites():
    session = MagicMock()
    session.get.return_value = _mock_response({"customer_satellites": []})
    client = isro.ISROClient(session=session)

    assert client.customer_satellites() == {"customer_satellites": []}
    args, _ = session.get.call_args
    assert args[0] == f"{isro.ISRO_API_BASE_URL}/customer_satellites"


def test_centres():
    session = MagicMock()
    session.get.return_value = _mock_response({"centres": []})
    client = isro.ISROClient(session=session)

    assert client.centres() == {"centres": []}
    args, _ = session.get.call_args
    assert args[0] == f"{isro.ISRO_API_BASE_URL}/centres"


def test_launches_previous_by_default():
    session = MagicMock()
    session.get.return_value = _mock_response({"results": []})
    client = isro.ISROClient(session=session)

    result = client.launches(limit=5)

    assert result == {"results": []}
    args, kwargs = session.get.call_args
    assert args[0] == f"{isro.LAUNCH_LIBRARY_BASE_URL}/launch/previous/"
    assert kwargs["params"]["lsp__id"] == isro.ISRO_AGENCY_ID
    assert kwargs["params"]["limit"] == 5
    assert "search" not in kwargs["params"]


def test_launches_upcoming_with_search():
    session = MagicMock()
    session.get.return_value = _mock_response({"results": []})
    client = isro.ISROClient(session=session)

    client.launches(upcoming=True, search="PSLV", offset=10)

    args, kwargs = session.get.call_args
    assert args[0] == f"{isro.LAUNCH_LIBRARY_BASE_URL}/launch/upcoming/"
    assert kwargs["params"]["search"] == "PSLV"
    assert kwargs["params"]["offset"] == 10


def test_agency():
    session = MagicMock()
    session.get.return_value = _mock_response({"id": isro.ISRO_AGENCY_ID})
    client = isro.ISROClient(session=session)

    assert client.agency() == {"id": isro.ISRO_AGENCY_ID}
    args, _ = session.get.call_args
    assert args[0] == (
        f"{isro.LAUNCH_LIBRARY_BASE_URL}/agencies/{isro.ISRO_AGENCY_ID}/"
    )


def test_celestrak_elements_by_norad_id():
    session = MagicMock()
    session.get.return_value = _mock_response([{"OBJECT_NAME": "CARTOSAT"}])
    client = isro.ISROClient(session=session)

    result = client.celestrak_elements(norad_id=41384)

    assert result == [{"OBJECT_NAME": "CARTOSAT"}]
    args, kwargs = session.get.call_args
    assert args[0] == isro.CELESTRAK_GP_URL
    assert kwargs["params"]["CATNR"] == 41384
    assert kwargs["params"]["FORMAT"] == "json"


def test_celestrak_elements_group_takes_precedence():
    session = MagicMock()
    session.get.return_value = _mock_response([])
    client = isro.ISROClient(session=session)

    client.celestrak_elements(norad_id=41384, group="gnss", name="IRNSS")

    _, kwargs = session.get.call_args
    assert kwargs["params"]["GROUP"] == "gnss"
    assert "CATNR" not in kwargs["params"]
    assert "NAME" not in kwargs["params"]


def test_celestrak_elements_text_format():
    session = MagicMock()
    session.get.return_value = _mock_response(text="ISRO TLE TEXT")
    client = isro.ISROClient(session=session)

    result = client.celestrak_elements(norad_id=41384, fmt="TLE")

    assert result == "ISRO TLE TEXT"
    _, kwargs = session.get.call_args
    assert kwargs["params"]["FORMAT"] == "tle"


def test_celestrak_elements_requires_selector():
    client = isro.ISROClient(session=MagicMock())

    with pytest.raises(ValueError):
        client.celestrak_elements()


def test_navic_elements():
    session = MagicMock()
    session.get.return_value = _mock_response([])
    client = isro.ISROClient(session=session)

    assert client.navic_elements() == []
    args, kwargs = session.get.call_args
    assert args[0] == isro.CELESTRAK_GP_URL
    assert kwargs["params"]["NAME"] == "IRNSS"


def test_error_response_raises():
    session = MagicMock()
    session.get.return_value = _mock_response(
        None, status_code=500, ok=False, text="Internal Server Error"
    )
    client = isro.ISROClient(session=session)

    with pytest.raises(isro.ISROAPIError):
        client.spacecrafts()


def test_error_response_raises_for_text_format():
    session = MagicMock()
    session.get.return_value = _mock_response(
        None, status_code=404, ok=False, text="Not Found"
    )
    client = isro.ISROClient(session=session)

    with pytest.raises(isro.ISROAPIError):
        client.celestrak_elements(norad_id=41384, fmt="tle")


def test_request_exception_raises_isro_error():
    session = MagicMock()
    session.get.side_effect = requests.ConnectionError("boom")
    client = isro.ISROClient(session=session)

    with pytest.raises(isro.ISROAPIError):
        client.launches()
