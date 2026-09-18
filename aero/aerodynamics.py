"""Basic aerodynamics helper functions."""

from __future__ import annotations

from . import atmosphere


def dynamic_pressure(rho: float, velocity: float) -> float:
    """Return dynamic pressure q = 1/2 * rho * V^2 (Pa)."""
    return 0.5 * rho * velocity**2


def lift(rho: float, velocity: float, area: float, cl: float) -> float:
    """Return lift force (N) for given density, velocity, wing area and CL."""
    return dynamic_pressure(rho, velocity) * area * cl


def drag(rho: float, velocity: float, area: float, cd: float) -> float:
    """Return drag force (N) for given density, velocity, wing area and CD."""
    return dynamic_pressure(rho, velocity) * area * cd


def lift_to_drag_ratio(cl: float, cd: float) -> float:
    """Return the lift-to-drag ratio L/D for given coefficients."""
    if cd == 0:
        raise ValueError("cd must be non-zero")
    return cl / cd


def mach_number(velocity: float, altitude: float = 0.0) -> float:
    """Return the Mach number for a velocity (m/s) at a given altitude (m)."""
    a = atmosphere.speed_of_sound(altitude)
    return velocity / a


def reynolds_number(
    rho: float, velocity: float, length: float, dynamic_viscosity: float
) -> float:
    """Return the Reynolds number Re = rho * V * L / mu."""
    if dynamic_viscosity <= 0:
        raise ValueError("dynamic_viscosity must be positive")
    return rho * velocity * length / dynamic_viscosity
