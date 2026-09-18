"""International Standard Atmosphere (ISA) model.

Implements the ISA model for the troposphere (0-11 km) and the first
layer of the stratosphere (11-20 km), which covers the altitude range
relevant to most subsonic and low-supersonic aircraft.
"""

from __future__ import annotations

import math

# Sea-level reference conditions.
T0 = 288.15  # Temperature at sea level, K
P0 = 101325.0  # Pressure at sea level, Pa
RHO0 = 1.225  # Density at sea level, kg/m^3

# Physical constants.
G0 = 9.80665  # Standard gravity, m/s^2
R = 287.05287  # Specific gas constant for air, J/(kg*K)
GAMMA = 1.4  # Ratio of specific heats for air

# Layer boundaries and lapse rates.
TROPOPAUSE_ALTITUDE = 11000.0  # m
TROPOPAUSE_TEMPERATURE = 216.65  # K
LAPSE_RATE_TROPOSPHERE = -0.0065  # K/m
STRATOSPHERE_LIMIT_ALTITUDE = 20000.0  # m


def temperature(altitude: float) -> float:
    """Return the ISA temperature (K) at the given geopotential altitude (m)."""
    if altitude < 0:
        raise ValueError("altitude must be non-negative")
    if altitude <= TROPOPAUSE_ALTITUDE:
        return T0 + LAPSE_RATE_TROPOSPHERE * altitude
    if altitude <= STRATOSPHERE_LIMIT_ALTITUDE:
        return TROPOPAUSE_TEMPERATURE
    raise ValueError("altitude must be <= 20000 m for this model")


def pressure(altitude: float) -> float:
    """Return the ISA pressure (Pa) at the given geopotential altitude (m)."""
    if altitude < 0:
        raise ValueError("altitude must be non-negative")
    if altitude <= TROPOPAUSE_ALTITUDE:
        t = temperature(altitude)
        exponent = -G0 / (LAPSE_RATE_TROPOSPHERE * R)
        return P0 * (t / T0) ** exponent
    if altitude <= STRATOSPHERE_LIMIT_ALTITUDE:
        p11 = pressure(TROPOPAUSE_ALTITUDE)
        return p11 * math.exp(
            -G0 * (altitude - TROPOPAUSE_ALTITUDE) / (R * TROPOPAUSE_TEMPERATURE)
        )
    raise ValueError("altitude must be <= 20000 m for this model")


def density(altitude: float) -> float:
    """Return the ISA density (kg/m^3) at the given geopotential altitude (m)."""
    return pressure(altitude) / (R * temperature(altitude))


def speed_of_sound(altitude: float) -> float:
    """Return the local speed of sound (m/s) at the given altitude (m)."""
    return math.sqrt(GAMMA * R * temperature(altitude))
