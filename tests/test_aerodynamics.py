import pytest

from aero import aerodynamics, atmosphere


def test_dynamic_pressure():
    q = aerodynamics.dynamic_pressure(1.225, 100.0)
    assert q == pytest.approx(0.5 * 1.225 * 100.0**2)


def test_lift_and_drag():
    rho = 1.225
    v = 100.0
    area = 20.0
    cl = 0.5
    cd = 0.05
    lift = aerodynamics.lift(rho, v, area, cl)
    drag = aerodynamics.drag(rho, v, area, cd)
    q = aerodynamics.dynamic_pressure(rho, v)
    assert lift == pytest.approx(q * area * cl)
    assert drag == pytest.approx(q * area * cd)


def test_lift_to_drag_ratio():
    assert aerodynamics.lift_to_drag_ratio(1.0, 0.05) == pytest.approx(20.0)


def test_lift_to_drag_ratio_zero_cd_raises():
    with pytest.raises(ValueError):
        aerodynamics.lift_to_drag_ratio(1.0, 0.0)


def test_mach_number_sea_level():
    a = atmosphere.speed_of_sound(0)
    assert aerodynamics.mach_number(a) == pytest.approx(1.0)
    assert aerodynamics.mach_number(a / 2) == pytest.approx(0.5)


def test_reynolds_number():
    rho = 1.225
    v = 50.0
    length = 1.0
    mu = 1.81e-5
    re = aerodynamics.reynolds_number(rho, v, length, mu)
    assert re == pytest.approx(rho * v * length / mu)


def test_reynolds_number_zero_viscosity_raises():
    with pytest.raises(ValueError):
        aerodynamics.reynolds_number(1.225, 50.0, 1.0, 0.0)
