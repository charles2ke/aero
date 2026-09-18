import math

import pytest

from aero import rocketry


def test_exhaust_velocity_and_specific_impulse_round_trip():
    ve = rocketry.exhaust_velocity(311.0)
    assert ve == pytest.approx(311.0 * rocketry.STANDARD_GRAVITY)
    assert rocketry.specific_impulse(ve) == pytest.approx(311.0)


def test_mass_ratio():
    assert rocketry.mass_ratio(1000.0, 250.0) == pytest.approx(4.0)


def test_delta_v_matches_rocket_equation():
    ve = rocketry.exhaust_velocity(300.0)
    dv = rocketry.delta_v(ve, 1000.0, 400.0)
    assert dv == pytest.approx(ve * math.log(2.5))


def test_propellant_mass_gives_requested_delta_v():
    ve = rocketry.exhaust_velocity(320.0)
    initial = 5000.0
    required = 2500.0
    propellant = rocketry.propellant_mass(ve, initial, required)
    assert rocketry.delta_v(ve, initial, initial - propellant) == pytest.approx(
        required
    )


def test_thrust_and_mass_flow_rate_are_inverse():
    ve = rocketry.exhaust_velocity(350.0)
    f = rocketry.thrust(250.0, ve)
    assert rocketry.mass_flow_rate(f, ve) == pytest.approx(250.0)


def test_burn_time():
    assert rocketry.burn_time(1200.0, 4.0) == pytest.approx(300.0)


def test_thrust_to_weight_ratio_at_liftoff():
    twr = rocketry.thrust_to_weight_ratio(7_600_000.0, 549_054.0)
    # Falcon 9 lifts off with a thrust-to-weight ratio of roughly 1.4.
    assert twr == pytest.approx(1.41, rel=1e-2)


def test_stage_delta_v_single_stage_matches_rocket_equation():
    ve = rocketry.exhaust_velocity(300.0)
    total = rocketry.stage_delta_v([(ve, 500.0, 4000.0)], payload_mass=1000.0)
    assert total == pytest.approx(rocketry.delta_v(ve, 5500.0, 1500.0))


def test_stage_delta_v_two_stages_beats_equivalent_single_stage():
    ve = rocketry.exhaust_velocity(300.0)
    staged = rocketry.stage_delta_v(
        [(ve, 400.0, 3600.0), (ve, 100.0, 900.0)], payload_mass=100.0
    )
    single = rocketry.delta_v(ve, 5100.0, 600.0)
    assert staged > single


def test_total_delta_v_sums_budget():
    assert rocketry.total_delta_v([9400.0, 1790.0, 680.0]) == pytest.approx(11870.0)


@pytest.mark.parametrize("value", [0, -1])
def test_non_positive_inputs_raise(value):
    with pytest.raises(ValueError):
        rocketry.exhaust_velocity(value)
    with pytest.raises(ValueError):
        rocketry.specific_impulse(value)
    with pytest.raises(ValueError):
        rocketry.mass_ratio(1000.0, value)
    with pytest.raises(ValueError):
        rocketry.thrust(value, 3000.0)
    with pytest.raises(ValueError):
        rocketry.burn_time(100.0, value)
    with pytest.raises(ValueError):
        rocketry.thrust_to_weight_ratio(1000.0, value)


def test_final_mass_above_initial_mass_raises():
    with pytest.raises(ValueError):
        rocketry.mass_ratio(100.0, 200.0)


def test_negative_delta_v_entries_raise():
    with pytest.raises(ValueError):
        rocketry.total_delta_v([100.0, -1.0])


def test_empty_stage_list_raises():
    with pytest.raises(ValueError):
        rocketry.stage_delta_v([])
