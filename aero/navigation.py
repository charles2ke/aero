"""Great-circle navigation: shortest paths over a spherical Earth.

The shortest path between two points on a sphere is the minor arc of the
great circle that passes through both of them. These helpers work with
geodetic latitude/longitude in degrees and return distances in meters,
bearings in degrees measured clockwise from true north.
"""

from __future__ import annotations

import math
from typing import List, Tuple

# Mean radius of the Earth, m (IUGG mean radius R1).
EARTH_MEAN_RADIUS = 6371008.8


def _validate_position(latitude: float, longitude: float) -> None:
    if not -90.0 <= latitude <= 90.0:
        raise ValueError("latitude must be between -90 and 90 degrees")
    if not -180.0 <= longitude <= 360.0:
        raise ValueError("longitude must be between -180 and 360 degrees")


def _validate_radius(radius: float) -> None:
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError("radius must be positive")


def central_angle(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Return the angle (radians) subtended at the center of the sphere.

    This is the angular length of the shortest (great-circle) path between
    the two positions, computed with the numerically stable haversine
    formula.
    """
    _validate_position(lat1, lon1)
    _validate_position(lat2, lon2)

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = phi2 - phi1
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    a = min(1.0, max(0.0, a))
    return 2.0 * math.asin(math.sqrt(a))


def great_circle_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    radius: float = EARTH_MEAN_RADIUS,
) -> float:
    """Return the shortest surface distance (m) between two positions."""
    _validate_radius(radius)
    return radius * central_angle(lat1, lon1, lat2, lon2)


def initial_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the initial course (degrees from true north) of the shortest path.

    The bearing of a great-circle route changes along the way; this is the
    heading to steer when departing the first position.
    """
    _validate_position(lat1, lon1)
    _validate_position(lat2, lon2)

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(
        delta_lambda
    )
    return math.degrees(math.atan2(y, x)) % 360.0


def final_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the course (degrees from true north) on arrival at the second point."""
    return (initial_bearing(lat2, lon2, lat1, lon1) + 180.0) % 360.0


def destination_point(
    lat: float,
    lon: float,
    bearing: float,
    distance: float,
    radius: float = EARTH_MEAN_RADIUS,
) -> Tuple[float, float]:
    """Return the position reached by travelling along a great circle.

    Starts at ``(lat, lon)``, departs on ``bearing`` degrees from true
    north, and follows the great circle for ``distance`` meters. Returns
    ``(latitude, longitude)`` in degrees, with longitude normalized to
    [-180, 180].
    """
    _validate_position(lat, lon)
    _validate_radius(radius)
    if distance < 0:
        raise ValueError("distance must be non-negative")

    phi1 = math.radians(lat)
    lambda1 = math.radians(lon)
    theta = math.radians(bearing)
    delta = distance / radius

    sin_phi2 = math.sin(phi1) * math.cos(delta) + math.cos(phi1) * math.sin(
        delta
    ) * math.cos(theta)
    sin_phi2 = min(1.0, max(-1.0, sin_phi2))
    phi2 = math.asin(sin_phi2)
    lambda2 = lambda1 + math.atan2(
        math.sin(theta) * math.sin(delta) * math.cos(phi1),
        math.cos(delta) - math.sin(phi1) * sin_phi2,
    )
    return math.degrees(phi2), (math.degrees(lambda2) + 540.0) % 360.0 - 180.0


def intermediate_point(
    lat1: float, lon1: float, lat2: float, lon2: float, fraction: float
) -> Tuple[float, float]:
    """Return the point a given fraction along the shortest path.

    ``fraction`` is 0.0 at the first position and 1.0 at the second.
    Raises ``ValueError`` when the positions are antipodal because their
    shortest path is not unique.
    """
    if not 0.0 <= fraction <= 1.0:
        raise ValueError("fraction must be between 0 and 1")

    delta = central_angle(lat1, lon1, lat2, lon2)
    phi1 = math.radians(lat1)
    lambda1 = math.radians(lon1)
    phi2 = math.radians(lat2)
    lambda2 = math.radians(lon2)

    if delta == 0.0:
        return lat1, (lon1 + 540.0) % 360.0 - 180.0
    if math.isclose(delta, math.pi, rel_tol=0.0, abs_tol=1e-7):
        raise ValueError("shortest path is undefined for antipodal positions")

    a = math.sin((1.0 - fraction) * delta) / math.sin(delta)
    b = math.sin(fraction * delta) / math.sin(delta)

    x = a * math.cos(phi1) * math.cos(lambda1) + b * math.cos(phi2) * math.cos(lambda2)
    y = a * math.cos(phi1) * math.sin(lambda1) + b * math.cos(phi2) * math.sin(lambda2)
    z = a * math.sin(phi1) + b * math.sin(phi2)

    phi = math.atan2(z, math.hypot(x, y))
    lam = math.atan2(y, x)
    return math.degrees(phi), (math.degrees(lam) + 540.0) % 360.0 - 180.0


def shortest_path(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    segments: int = 16,
) -> List[Tuple[float, float]]:
    """Return points sampling the shortest path between two positions.

    The returned list contains ``segments + 1`` ``(latitude, longitude)``
    pairs, starting at the first position and ending at the second.
    """
    if segments < 1:
        raise ValueError("segments must be at least 1")
    return [
        intermediate_point(lat1, lon1, lat2, lon2, i / segments)
        for i in range(segments + 1)
    ]
