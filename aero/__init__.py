"""aero: a small library of common aerospace engineering calculations."""

from . import aerodynamics, atmosphere, esa, iss, isro, nasa, orbital

__version__ = "0.1.0"

__all__ = [
    "aerodynamics",
    "atmosphere",
    "esa",
    "iss",
    "isro",
    "nasa",
    "orbital",
    "__version__",
]
