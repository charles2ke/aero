import math

import pytest

from aero import navigation

# Approximate airport positions used as reference routes.
JFK = (40.6413, -73.7781)
LHR = (51.4700, -0.4543)
LAX = (33.9416, -118.4085)


def test_great_circle_distance_jfk_to_lhr():
    d = navigation.great_circle_distance(*JFK, *LHR)
    # The JFK-London Heathrow great-circle route is about 5540 km.
    assert d == pytest.approx(5_540_000, rel=1e-2)


def test_distance_is_symmetric():
    forward = navigation.great_circle_distance(*JFK, *LAX)
    backward = navigation.great_circle_distance(*LAX, *JFK)
    assert forward == pytest.approx(backward)


def test_distance_to_same_point_is_zero():
    assert navigation.great_circle_distance(*JFK, *JFK) == pytest.approx(0.0)


def test_antipodal_distance_is_half_circumference():
    d = navigation.great_circle_distance(0.0, 0.0, 0.0, 180.0)
    assert d == pytest.approx(math.pi * navigation.EARTH_MEAN_RADIUS)


def test_distance_along_equator_matches_arc_length():
    d = navigation.great_circle_distance(0.0, 0.0, 0.0, 90.0)
    assert d == pytest.approx(navigation.EARTH_MEAN_RADIUS * math.pi / 2.0)


def test_initial_bearing_due_north():
    assert navigation.initial_bearing(0.0, 0.0, 10.0, 0.0) == pytest.approx(0.0)


def test_initial_bearing_due_east_on_equator():
    assert navigation.initial_bearing(0.0, 0.0, 0.0, 10.0) == pytest.approx(90.0)


def test_initial_bearing_jfk_to_lhr_is_north_easterly():
    bearing = navigation.initial_bearing(*JFK, *LHR)
    assert bearing == pytest.approx(51.4, abs=1.0)


def test_final_bearing_differs_from_initial_on_long_route():
    initial = navigation.initial_bearing(*JFK, *LHR)
    final = navigation.final_bearing(*JFK, *LHR)
    assert final > initial


def test_destination_point_round_trip():
    distance = navigation.great_circle_distance(*JFK, *LHR)
    bearing = navigation.initial_bearing(*JFK, *LHR)
    lat, lon = navigation.destination_point(*JFK, bearing, distance)
    assert lat == pytest.approx(LHR[0], abs=1e-6)
    assert lon == pytest.approx(LHR[1], abs=1e-6)


def test_destination_point_zero_distance_returns_origin():
    lat, lon = navigation.destination_point(*JFK, 123.0, 0.0)
    assert (lat, lon) == pytest.approx(JFK)


def test_intermediate_point_endpoints():
    start = navigation.intermediate_point(*JFK, *LHR, 0.0)
    end = navigation.intermediate_point(*JFK, *LHR, 1.0)
    assert start == pytest.approx(JFK, abs=1e-9)
    assert end == pytest.approx(LHR, abs=1e-9)


def test_intermediate_point_halves_the_distance():
    mid = navigation.intermediate_point(*JFK, *LHR, 0.5)
    total = navigation.great_circle_distance(*JFK, *LHR)
    first_leg = navigation.great_circle_distance(*JFK, *mid)
    assert first_leg == pytest.approx(total / 2.0)


def test_intermediate_point_same_position():
    assert navigation.intermediate_point(*JFK, *JFK, 0.5) == pytest.approx(JFK)


def test_shortest_path_sampling():
    path = navigation.shortest_path(*JFK, *LHR, segments=4)
    assert len(path) == 5
    assert path[0] == pytest.approx(JFK, abs=1e-9)
    assert path[-1] == pytest.approx(LHR, abs=1e-9)
    # A great-circle route from JFK to London arcs north of both endpoints.
    assert max(lat for lat, _ in path) > max(JFK[0], LHR[0])


def test_shortest_path_legs_sum_to_total_distance():
    path = navigation.shortest_path(*JFK, *LAX, segments=8)
    total = navigation.great_circle_distance(*JFK, *LAX)
    legs = sum(
        navigation.great_circle_distance(*a, *b) for a, b in zip(path, path[1:])
    )
    assert legs == pytest.approx(total)


def test_custom_radius_scales_distance():
    d_earth = navigation.great_circle_distance(0.0, 0.0, 0.0, 90.0)
    d_half = navigation.great_circle_distance(
        0.0, 0.0, 0.0, 90.0, radius=navigation.EARTH_MEAN_RADIUS / 2.0
    )
    assert d_half == pytest.approx(d_earth / 2.0)


@pytest.mark.parametrize(
    "lat, lon",
    [(91.0, 0.0), (-91.0, 0.0), (0.0, -181.0), (0.0, 361.0)],
)
def test_invalid_positions_raise(lat, lon):
    with pytest.raises(ValueError):
        navigation.great_circle_distance(lat, lon, 0.0, 0.0)


def test_invalid_radius_raises():
    with pytest.raises(ValueError):
        navigation.great_circle_distance(*JFK, *LHR, radius=0.0)


def test_negative_distance_raises():
    with pytest.raises(ValueError):
        navigation.destination_point(*JFK, 90.0, -1.0)


def test_invalid_fraction_raises():
    with pytest.raises(ValueError):
        navigation.intermediate_point(*JFK, *LHR, 1.5)


def test_invalid_segments_raises():
    with pytest.raises(ValueError):
        navigation.shortest_path(*JFK, *LHR, segments=0)
