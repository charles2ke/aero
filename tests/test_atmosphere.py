import math

import pytest

from aero import atmosphere


def test_sea_level_conditions():
    assert atmosphere.temperature(0) == pytest.approx(288.15)
    assert atmosphere.pressure(0) == pytest.approx(101325.0)
    assert atmosphere.density(0) == pytest.approx(1.225, rel=1e-3)


def test_temperature_decreases_with_altitude_in_troposphere():
    t_ground = atmosphere.temperature(0)
    t_5000 = atmosphere.temperature(5000)
    t_11000 = atmosphere.temperature(11000)
    assert t_ground > t_5000 > t_11000
    assert t_11000 == pytest.approx(216.65)


def test_temperature_constant_in_lower_stratosphere():
    assert atmosphere.temperature(11000) == pytest.approx(216.65)
    assert atmosphere.temperature(15000) == pytest.approx(216.65)
    assert atmosphere.temperature(20000) == pytest.approx(216.65)


def test_pressure_decreases_monotonically():
    altitudes = [0, 1000, 5000, 11000, 15000, 20000]
    pressures = [atmosphere.pressure(a) for a in altitudes]
    assert pressures == sorted(pressures, reverse=True)


def test_pressure_known_value_at_11km():
    # Known ISA value at the tropopause is approximately 22632 Pa.
    assert atmosphere.pressure(11000) == pytest.approx(22632, rel=1e-3)


def test_density_known_value_at_11km():
    # Known ISA value at the tropopause is approximately 0.3639 kg/m^3.
    assert atmosphere.density(11000) == pytest.approx(0.3639, rel=1e-3)


def test_speed_of_sound_sea_level():
    assert atmosphere.speed_of_sound(0) == pytest.approx(340.3, rel=1e-3)


def test_negative_altitude_raises():
    with pytest.raises(ValueError):
        atmosphere.temperature(-100)
    with pytest.raises(ValueError):
        atmosphere.pressure(-100)


def test_altitude_above_model_limit_raises():
    with pytest.raises(ValueError):
        atmosphere.temperature(20001)
    with pytest.raises(ValueError):
        atmosphere.pressure(20001)
