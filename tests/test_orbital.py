import math

import pytest

from aero import orbital


def test_circular_orbital_velocity_low_earth_orbit():
    radius = orbital.EARTH_RADIUS + 400000.0  # 400 km altitude, like the ISS
    v = orbital.circular_orbital_velocity(orbital.EARTH_MU, radius)
    # ISS orbital speed is approximately 7.66 km/s.
    assert v == pytest.approx(7660, rel=1e-2)


def test_orbital_velocity_matches_circular_case():
    radius = orbital.EARTH_RADIUS + 400000.0
    v_vis_viva = orbital.orbital_velocity(orbital.EARTH_MU, radius, radius)
    v_circular = orbital.circular_orbital_velocity(orbital.EARTH_MU, radius)
    assert v_vis_viva == pytest.approx(v_circular)


def test_orbital_period_matches_known_value():
    # Geostationary orbit period should be one sidereal day (~86164 s).
    geo_radius = 42164000.0
    period = orbital.orbital_period(orbital.EARTH_MU, geo_radius)
    assert period == pytest.approx(86164, rel=1e-3)


def test_escape_velocity_earth_surface():
    v_esc = orbital.escape_velocity(orbital.EARTH_MU, orbital.EARTH_RADIUS)
    assert v_esc == pytest.approx(11186, rel=1e-3)


def test_escape_velocity_is_sqrt2_times_circular_velocity():
    radius = orbital.EARTH_RADIUS + 400000.0
    v_circular = orbital.circular_orbital_velocity(orbital.EARTH_MU, radius)
    v_esc = orbital.escape_velocity(orbital.EARTH_MU, radius)
    assert v_esc == pytest.approx(v_circular * math.sqrt(2))


@pytest.mark.parametrize("radius", [0, -1])
def test_non_positive_radius_raises(radius):
    with pytest.raises(ValueError):
        orbital.circular_orbital_velocity(orbital.EARTH_MU, radius)
    with pytest.raises(ValueError):
        orbital.escape_velocity(orbital.EARTH_MU, radius)
