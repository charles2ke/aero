"""Rocket science helper functions.

Covers the ideal rocket (Tsiolkovsky) equation, propellant mass ratios,
engine performance (thrust, specific impulse, exhaust velocity), burn
time, thrust-to-weight ratio, and multi-stage delta-v budgets.

Masses are in kilograms, velocities in m/s, thrust in newtons, mass flow
rates in kg/s and times in seconds.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence, Tuple

# Standard gravity used to define specific impulse, m/s^2.
STANDARD_GRAVITY = 9.80665


def exhaust_velocity(specific_impulse: float, g0: float = STANDARD_GRAVITY) -> float:
    """Return effective exhaust velocity (m/s) for a specific impulse (s)."""
    if specific_impulse <= 0:
        raise ValueError("specific_impulse must be positive")
    if g0 <= 0:
        raise ValueError("g0 must be positive")
    return specific_impulse * g0


def specific_impulse(exhaust_speed: float, g0: float = STANDARD_GRAVITY) -> float:
    """Return specific impulse (s) for an effective exhaust velocity (m/s)."""
    if exhaust_speed <= 0:
        raise ValueError("exhaust_speed must be positive")
    if g0 <= 0:
        raise ValueError("g0 must be positive")
    return exhaust_speed / g0


def mass_ratio(initial_mass: float, final_mass: float) -> float:
    """Return the mass ratio ``m0 / mf`` of a rocket or stage."""
    if initial_mass <= 0 or final_mass <= 0:
        raise ValueError("initial_mass and final_mass must be positive")
    if final_mass > initial_mass:
        raise ValueError("final_mass must not exceed initial_mass")
    return initial_mass / final_mass


def delta_v(
    exhaust_speed: float, initial_mass: float, final_mass: float
) -> float:
    """Return the ideal delta-v (m/s) from the Tsiolkovsky rocket equation.

    ``exhaust_speed`` is the effective exhaust velocity (m/s); use
    :func:`exhaust_velocity` to convert from specific impulse.
    """
    if exhaust_speed <= 0:
        raise ValueError("exhaust_speed must be positive")
    return exhaust_speed * math.log(mass_ratio(initial_mass, final_mass))


def propellant_mass(
    exhaust_speed: float, initial_mass: float, required_delta_v: float
) -> float:
    """Return the propellant mass (kg) needed for ``required_delta_v`` (m/s)."""
    if exhaust_speed <= 0:
        raise ValueError("exhaust_speed must be positive")
    if initial_mass <= 0:
        raise ValueError("initial_mass must be positive")
    if required_delta_v < 0:
        raise ValueError("required_delta_v must not be negative")
    return initial_mass * (1.0 - math.exp(-required_delta_v / exhaust_speed))


def thrust(mass_flow_rate: float, exhaust_speed: float) -> float:
    """Return thrust (N) produced by a mass flow rate (kg/s) of propellant."""
    if mass_flow_rate <= 0:
        raise ValueError("mass_flow_rate must be positive")
    if exhaust_speed <= 0:
        raise ValueError("exhaust_speed must be positive")
    return mass_flow_rate * exhaust_speed


def mass_flow_rate(thrust_force: float, exhaust_speed: float) -> float:
    """Return the propellant mass flow rate (kg/s) for a given thrust (N)."""
    if thrust_force <= 0:
        raise ValueError("thrust_force must be positive")
    if exhaust_speed <= 0:
        raise ValueError("exhaust_speed must be positive")
    return thrust_force / exhaust_speed


def burn_time(propellant: float, flow_rate: float) -> float:
    """Return the burn time (s) for a propellant mass (kg) and flow rate (kg/s)."""
    if propellant < 0:
        raise ValueError("propellant must not be negative")
    if flow_rate <= 0:
        raise ValueError("flow_rate must be positive")
    return propellant / flow_rate


def thrust_to_weight_ratio(
    thrust_force: float, mass: float, gravity: float = STANDARD_GRAVITY
) -> float:
    """Return the (dimensionless) thrust-to-weight ratio of a vehicle."""
    if thrust_force < 0:
        raise ValueError("thrust_force must not be negative")
    if mass <= 0:
        raise ValueError("mass must be positive")
    if gravity <= 0:
        raise ValueError("gravity must be positive")
    return thrust_force / (mass * gravity)


def stage_delta_v(
    stages: Sequence[Tuple[float, float, float]], payload_mass: float = 0.0
) -> float:
    """Return the total ideal delta-v (m/s) of a serially staged rocket.

    ``stages`` is an ordered sequence of ``(exhaust_speed, structural_mass,
    propellant_mass)`` tuples, from the first stage burned to the last.
    Each stage carries the payload and all later stages as its own payload.
    """
    stage_list = list(stages)
    if not stage_list:
        raise ValueError("stages must not be empty")
    if payload_mass < 0:
        raise ValueError("payload_mass must not be negative")

    for _, structural, propellant in stage_list:
        if structural <= 0:
            raise ValueError("structural mass must be positive")
        if propellant <= 0:
            raise ValueError("propellant mass must be positive")

    total = 0.0
    carried = payload_mass
    for index in range(len(stage_list) - 1, -1, -1):
        exhaust_speed, structural, propellant = stage_list[index]
        initial = carried + structural + propellant
        final = carried + structural
        total += delta_v(exhaust_speed, initial, final)
        carried = initial
    return total


def total_delta_v(delta_vs: Iterable[float]) -> float:
    """Return the sum of a delta-v budget (m/s), rejecting negative entries."""
    total = 0.0
    for value in delta_vs:
        if value < 0:
            raise ValueError("delta-v entries must not be negative")
        total += value
    return total
