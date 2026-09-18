"""Browser tests for the static website in ``website/``.

These tests are skipped unless Playwright and its Chromium browser are
installed (``pip install playwright && playwright install chromium``).
"""

from __future__ import annotations

import pathlib

import pytest

sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright

INDEX = pathlib.Path(__file__).resolve().parent.parent / "website" / "index.html"


@pytest.fixture(scope="module")
def page():
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch()
        except Exception as exc:  # pragma: no cover - browser not installed
            pytest.skip(f"Chromium is not available: {exc}")
        page = browser.new_page()
        page.goto(INDEX.as_uri())
        yield page
        browser.close()


def test_hero_and_sections_render(page):
    assert page.inner_text("h1") == "aero"
    for anchor in ("#modules", "#calculators", "#data", "#install"):
        assert page.locator(anchor).count() == 1


def test_atmosphere_calculator_matches_library(page):
    from aero import atmosphere

    page.fill("#alt", "5000")
    page.dispatch_event("#alt", "input")
    text = page.inner_text("#atmosphere-output")
    assert f"{atmosphere.temperature(5000):.2f} K" in text
    assert f"{atmosphere.density(5000):.4f} kg/m" in text
    assert f"{atmosphere.speed_of_sound(5000):.2f} m/s" in text


def test_atmosphere_calculator_reports_out_of_range_altitude(page):
    page.fill("#alt", "25000")
    page.dispatch_event("#alt", "input")
    assert "20000" in page.inner_text("#atmosphere-output")


def test_orbital_calculator_matches_library(page):
    from aero import orbital

    page.fill("#orb-alt", "400")
    page.dispatch_event("#orb-alt", "input")
    radius = orbital.EARTH_RADIUS + 400_000
    text = page.inner_text("#orbital-output")
    assert f"{orbital.circular_orbital_velocity(orbital.EARTH_MU, radius):.1f} m/s" in text
    assert f"{orbital.orbital_period(orbital.EARTH_MU, radius) / 60:.2f} min" in text
