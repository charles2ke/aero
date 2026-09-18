"""Basic orbital mechanics helper functions.

All functions assume a two-body Keplerian orbit around a central body,
with distances in meters and the standard gravitational parameter
``mu = G * M`` in m^3/s^2.
"""

from __future__ import annotations

import math

# Standard gravitational parameter of Earth, m^3/s^2.
EARTH_MU = 3.986004418e14
EARTH_RADIUS = 6378137.0  # m


def orbital_velocity(mu: float, radius: float, semi_major_axis: float) -> float:
    """Return orbital speed (m/s) via the vis-viva equation.

    ``radius`` is the current distance from the central body and
    ``semi_major_axis`` is the semi-major axis of the orbit. For a
    circular orbit, ``radius == semi_major_axis``.
    """
    if radius <= 0 or semi_major_axis <= 0:
        raise ValueError("radius and semi_major_axis must be positive")
    return math.sqrt(mu * (2.0 / radius - 1.0 / semi_major_axis))


def circular_orbital_velocity(mu: float, radius: float) -> float:
    """Return the speed (m/s) required for a circular orbit of given radius."""
    if radius <= 0:
        raise ValueError("radius must be positive")
    return math.sqrt(mu / radius)


def orbital_period(mu: float, semi_major_axis: float) -> float:
    """Return the orbital period (s) for a given semi-major axis (m)."""
    if semi_major_axis <= 0:
        raise ValueError("semi_major_axis must be positive")
    return 2.0 * math.pi * math.sqrt(semi_major_axis**3 / mu)


def escape_velocity(mu: float, radius: float) -> float:
    """Return the escape velocity (m/s) at a given radius (m)."""
    if radius <= 0:
        raise ValueError("radius must be positive")
    return math.sqrt(2.0 * mu / radius)
