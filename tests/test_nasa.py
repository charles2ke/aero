"""Tests for aero.nasa connectivity to NASA program APIs.

All HTTP calls are mocked so the tests run offline and deterministically.
"""

from unittest.mock import MagicMock, patch

import pytest

from aero import nasa


def _mock_response(json_data, status_code=200, ok=True, text=""):
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.status_code = status_code
    resp.ok = ok
    resp.text = text
    return resp


def test_default_api_key_is_demo_key(monkeypatch):
    monkeypatch.delenv("NASA_API_KEY", raising=False)
    client = nasa.NASAClient()
    assert client.api_key == nasa.DEMO_KEY


def test_api_key_from_env(monkeypatch):
    monkeypatch.setenv("NASA_API_KEY", "abc123")
    client = nasa.NASAClient()
    assert client.api_key == "abc123"


def test_explicit_api_key_overrides_env(monkeypatch):
    monkeypatch.setenv("NASA_API_KEY", "abc123")
    client = nasa.NASAClient(api_key="explicit-key")
    assert client.api_key == "explicit-key"


def test_apod():
    session = MagicMock()
    session.get.return_value = _mock_response({"title": "A picture"})
    client = nasa.NASAClient(api_key="test-key", session=session)

    result = client.apod(date="2024-01-01")

    assert result == {"title": "A picture"}
    args, kwargs = session.get.call_args
    assert args[0] == f"{nasa.NASA_API_BASE_URL}/planetary/apod"
    assert kwargs["params"]["date"] == "2024-01-01"
    assert kwargs["params"]["api_key"] == "test-key"


def test_mars_rover_photos():
    session = MagicMock()
    session.get.return_value = _mock_response({"photos": []})
    client = nasa.NASAClient(api_key="test-key", session=session)

    result = client.mars_rover_photos(rover="curiosity", sol=1000, camera="FHAZ")

    assert result == {"photos": []}
    args, kwargs = session.get.call_args
    assert args[0] == (
        f"{nasa.NASA_API_BASE_URL}/mars-photos/api/v1/rovers/curiosity/photos"
    )
    assert kwargs["params"]["sol"] == 1000
    assert kwargs["params"]["camera"] == "FHAZ"


def test_neo_feed():
    session = MagicMock()
    session.get.return_value = _mock_response({"near_earth_objects": {}})
    client = nasa.NASAClient(api_key="test-key", session=session)

    result = client.neo_feed(start_date="2024-01-01", end_date="2024-01-02")

    assert result == {"near_earth_objects": {}}
    args, kwargs = session.get.call_args
    assert args[0] == f"{nasa.NASA_API_BASE_URL}/neo/rest/v1/feed"
    assert kwargs["params"]["start_date"] == "2024-01-01"
    assert kwargs["params"]["end_date"] == "2024-01-02"


def test_neo_lookup():
    session = MagicMock()
    session.get.return_value = _mock_response({"id": "3542519"})
    client = nasa.NASAClient(api_key="test-key", session=session)

    result = client.neo_lookup("3542519")

    assert result == {"id": "3542519"}
    args, _ = session.get.call_args
    assert args[0] == f"{nasa.NASA_API_BASE_URL}/neo/rest/v1/neo/3542519"


def test_donki_notifications():
    session = MagicMock()
    session.get.return_value = _mock_response([{"messageType": "FLR"}])
    client = nasa.NASAClient(api_key="test-key", session=session)

    result = client.donki_notifications(start_date="2024-01-01")

    assert result == [{"messageType": "FLR"}]
    args, kwargs = session.get.call_args
    assert args[0] == f"{nasa.NASA_API_BASE_URL}/DONKI/notifications"
    assert kwargs["params"]["startDate"] == "2024-01-01"
    assert kwargs["params"]["type"] == "all"


def test_epic_natural_images_with_date():
    session = MagicMock()
    session.get.return_value = _mock_response([{"identifier": "abc"}])
    client = nasa.NASAClient(api_key="test-key", session=session)

    result = client.epic_natural_images(date="2024-01-01")

    assert result == [{"identifier": "abc"}]
    args, _ = session.get.call_args
    assert args[0] == f"{nasa.NASA_API_BASE_URL}/EPIC/api/natural/date/2024-01-01"


def test_epic_natural_images_without_date():
    session = MagicMock()
    session.get.return_value = _mock_response([])
    client = nasa.NASAClient(api_key="test-key", session=session)

    client.epic_natural_images()

    args, _ = session.get.call_args
    assert args[0] == f"{nasa.NASA_API_BASE_URL}/EPIC/api/natural"


def test_insight_weather():
    session = MagicMock()
    session.get.return_value = _mock_response({"sol_keys": []})
    client = nasa.NASAClient(api_key="test-key", session=session)

    result = client.insight_weather()

    assert result == {"sol_keys": []}
    args, kwargs = session.get.call_args
    assert args[0] == f"{nasa.NASA_API_BASE_URL}/insight_weather/"
    assert kwargs["params"]["feedtype"] == "json"


def test_techport_projects():
    session = MagicMock()
    session.get.return_value = _mock_response({"projects": []})
    client = nasa.NASAClient(api_key="test-key", session=session)

    result = client.techport_projects(updated_since="2024-01-01T00:00:00Z")

    assert result == {"projects": []}
    args, kwargs = session.get.call_args
    assert args[0] == f"{nasa.NASA_API_BASE_URL}/techport/api/projects"
    assert kwargs["params"]["updatedSince"] == "2024-01-01T00:00:00Z"


def test_techport_project():
    session = MagicMock()
    session.get.return_value = _mock_response({"project": {"id": 12345}})
    client = nasa.NASAClient(api_key="test-key", session=session)

    result = client.techport_project(12345)

    assert result == {"project": {"id": 12345}}
    args, _ = session.get.call_args
    assert args[0] == f"{nasa.NASA_API_BASE_URL}/techport/api/projects/12345"


def test_exoplanets():
    session = MagicMock()
    session.get.return_value = _mock_response([{"pl_name": "Kepler-22 b"}])
    client = nasa.NASAClient(api_key="test-key", session=session)

    result = client.exoplanets(query="select pl_name from ps")

    assert result == [{"pl_name": "Kepler-22 b"}]
    args, kwargs = session.get.call_args
    assert args[0] == nasa.EXOPLANET_ARCHIVE_BASE_URL
    assert kwargs["params"]["query"] == "select pl_name from ps"
    # The Exoplanet Archive does not require an API key.
    assert "api_key" not in kwargs["params"]


def test_error_response_raises():
    session = MagicMock()
    session.get.return_value = _mock_response(
        None, status_code=403, ok=False, text="Forbidden"
    )
    client = nasa.NASAClient(api_key="bad-key", session=session)

    with pytest.raises(nasa.NASAAPIError):
        client.apod()


def test_request_exception_raises_nasa_error():
    import requests

    session = MagicMock()
    session.get.side_effect = requests.ConnectionError("boom")
    client = nasa.NASAClient(api_key="test-key", session=session)

    with pytest.raises(nasa.NASAAPIError):
        client.apod()


def test_exoplanet_error_response_raises():
    session = MagicMock()
    session.get.return_value = _mock_response(
        None, status_code=500, ok=False, text="Internal Server Error"
    )
    client = nasa.NASAClient(api_key="test-key", session=session)

    with pytest.raises(nasa.NASAAPIError):
        client.exoplanets()
