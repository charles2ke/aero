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


@pytest.fixture(scope="module")
def mobile_page(page):
    mobile = page.context.browser.new_page(
        viewport={"width": 320, "height": 568},
        is_mobile=True,
        has_touch=True,
    )
    mobile.goto(INDEX.as_uri())
    yield mobile
    mobile.close()


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


def test_aerodynamics_calculator_matches_library(page):
    from aero import aerodynamics, atmosphere

    altitude = 5000
    velocity = 120.0
    area = 16.2
    cl = 0.4
    cd = 0.03
    page.fill("#aero-alt", str(altitude))
    page.fill("#aero-v", str(velocity))
    page.fill("#aero-area", str(area))
    page.fill("#aero-cl", str(cl))
    page.fill("#aero-cd", str(cd))
    page.dispatch_event("#aero-cd", "input")
    rho = atmosphere.density(altitude)
    text = page.inner_text("#aero-output")
    assert f"{aerodynamics.dynamic_pressure(rho, velocity):.1f} Pa" in text
    assert f"{aerodynamics.lift(rho, velocity, area, cl):.1f} N" in text
    assert f"{aerodynamics.drag(rho, velocity, area, cd):.1f} N" in text
    assert f"{aerodynamics.lift_to_drag_ratio(cl, cd):.2f}" in text
    assert f"{aerodynamics.mach_number(velocity, altitude):.3f}" in text


def test_orbital_calculator_matches_library(page):
    from aero import orbital

    page.fill("#orb-alt", "400")
    page.dispatch_event("#orb-alt", "input")
    radius = orbital.EARTH_RADIUS + 400_000
    text = page.inner_text("#orbital-output")
    assert f"{orbital.circular_orbital_velocity(orbital.EARTH_MU, radius):.1f} m/s" in text
    assert f"{orbital.orbital_period(orbital.EARTH_MU, radius) / 60:.2f} min" in text
    assert f"{orbital.escape_velocity(orbital.EARTH_MU, radius):.1f} m/s" in text


def test_rocketry_calculator_matches_library(page):
    from aero import rocketry

    isp = 300.0
    m0 = 5500.0
    mf = 1500.0
    thrust_force = 7_600_000.0
    page.fill("#rkt-isp", str(isp))
    page.fill("#rkt-m0", str(m0))
    page.fill("#rkt-mf", str(mf))
    page.fill("#rkt-thrust", str(thrust_force))
    page.dispatch_event("#rkt-thrust", "input")
    ve = rocketry.exhaust_velocity(isp)
    flow = rocketry.mass_flow_rate(thrust_force, ve)
    text = page.inner_text("#rocketry-output")
    assert f"{ve:.1f} m/s" in text
    assert f"{rocketry.mass_ratio(m0, mf):.3f}" in text
    assert f"{rocketry.delta_v(ve, m0, mf):.1f} m/s" in text
    assert f"{flow:.2f} kg/s" in text
    assert f"{rocketry.burn_time(m0 - mf, flow):.1f} s" in text
    assert f"{rocketry.thrust_to_weight_ratio(thrust_force, m0):.2f}" in text


def test_rocketry_calculator_reports_invalid_masses(page):
    page.fill("#rkt-mf", "9000")
    page.dispatch_event("#rkt-mf", "input")
    assert "final_mass" in page.inner_text("#rocketry-output")
    page.fill("#rkt-mf", "1500")
    page.dispatch_event("#rkt-mf", "input")


def test_every_module_has_a_try_it_link(page):
    targets = [
        "#atmosphere-form",
        "#aero-form",
        "#orbital-form",
        "#rocketry-form",
        "#nasa-explorer",
        "#esa-explorer",
        "#iss-explorer",
        "#isro-explorer",
    ]
    for target in targets:
        assert page.locator(f'.try-link[href="{target}"]').count() == 1
        assert page.locator(target).count() == 1


def test_data_service_explorers_build_requests(page):
    from aero import esa, iss, isro, nasa

    expected_hosts = {
        "#nasa-explorer": nasa.NASA_API_BASE_URL,
        "#esa-explorer": esa.ESA_OPEN_DATA_BASE_URL,
        "#iss-explorer": iss.OPEN_NOTIFY_BASE_URL,
        "#isro-explorer": isro.ISRO_API_BASE_URL,
    }
    for selector, base_url in expected_hosts.items():
        assert page.locator(f"{selector} .explorer-endpoint option").count() >= 4
        url = page.inner_text(f"{selector} .explorer-url")
        assert url.startswith(base_url)
        assert page.inner_text(f"{selector} .explorer-snippet").strip()


def test_explorer_updates_url_when_endpoint_changes(page):
    from aero import iss

    page.select_option("#iss-explorer .explorer-endpoint", label=iss_astros_label(page))
    assert "astros.json" in page.inner_text("#iss-explorer .explorer-url")
    assert iss.OPEN_NOTIFY_BASE_URL in page.inner_text("#iss-explorer .explorer-url")
    page.select_option("#iss-explorer .explorer-endpoint", index=0)


def iss_astros_label(page):
    options = page.locator("#iss-explorer .explorer-endpoint option")
    for index in range(options.count()):
        label = options.nth(index).inner_text()
        if "people_in_space" in label:
            return label
    raise AssertionError("people_in_space endpoint is missing")


def test_reveal_animation_does_not_hide_content(page):
    page.locator("#explorer").scroll_into_view_if_needed()
    page.wait_for_timeout(1000)
    opacities = page.eval_on_selector_all(
        ".card, .calculator, .explorer",
        "els => els.map(el => getComputedStyle(el).opacity)",
    )
    assert opacities
    assert all(float(value) > 0.99 for value in opacities)


def test_landmarks_and_skip_link(page):
    assert page.locator("main#main").count() == 1
    assert page.locator("nav[aria-label]").count() == 1
    skip = page.locator(".skip-link")
    assert skip.get_attribute("href") == "#main"
    skip.focus()
    page.wait_for_timeout(400)
    box = skip.bounding_box()
    assert box is not None and box["y"] >= 0


def test_every_element_id_is_unique(page):
    duplicates = page.evaluate(
        "() => { const ids = [...document.querySelectorAll('[id]')].map(el => el.id);"
        " return ids.filter((id, index) => ids.indexOf(id) !== index); }"
    )
    assert duplicates == []


def test_form_controls_and_outputs_have_accessible_names(page):
    unnamed = page.evaluate(
        "() => [...document.querySelectorAll('input, select, output')]"
        ".filter(el => !(el.getAttribute('aria-label')"
        " || (el.labels && el.labels.length)))"
        ".map(el => el.outerHTML)"
    )
    assert unnamed == []


def test_repeated_links_and_buttons_have_unique_names(page):
    assert page.get_by_role("link", name="Try it with aero.orbital").count() == 1
    assert page.get_by_role("button", name="Send request for aero.iss").count() == 1


def test_scrollable_code_regions_are_keyboard_reachable(page):
    missing = page.evaluate(
        "() => [...document.querySelectorAll('pre.code')]"
        ".filter(el => el.tabIndex !== 0).length"
    )
    assert missing == 0


def test_calculator_error_is_announced_and_marks_the_input(page):
    page.fill("#alt", "")
    page.dispatch_event("#alt", "input")
    output = page.locator("#atmosphere-output")
    assert output.get_attribute("role") == "status"
    assert page.inner_text("#atmosphere-output").startswith("Error:")
    assert page.get_attribute("#alt", "aria-invalid") == "true"
    assert page.get_attribute("#alt", "aria-describedby") == "atmosphere-output"
    page.fill("#alt", "5000")
    page.dispatch_event("#alt", "input")
    assert page.get_attribute("#alt", "aria-invalid") is None


def test_decorative_icons_are_hidden_from_assistive_technology(page):
    exposed = page.evaluate(
        "() => [...document.querySelectorAll('svg.icon')]"
        ".filter(el => el.getAttribute('aria-hidden') !== 'true').length"
    )
    assert exposed == 0


def test_mobile_layout_has_no_horizontal_overflow(mobile_page):
    widths = mobile_page.evaluate(
        "() => ({scroll: document.documentElement.scrollWidth,"
        " client: document.documentElement.clientWidth})"
    )
    assert widths["scroll"] <= widths["client"]


def test_mobile_form_controls_avoid_ios_zoom(mobile_page):
    smallest = mobile_page.evaluate(
        "() => Math.min(...[...document.querySelectorAll('input, select')]"
        ".map(el => parseFloat(getComputedStyle(el).fontSize)))"
    )
    assert smallest >= 16


def test_mobile_tap_targets_are_large_enough(mobile_page):
    small = mobile_page.evaluate(
        "() => [...document.querySelectorAll('a, button, input, select')]"
        ".filter(el => { const r = el.getBoundingClientRect();"
        " return r.width > 0 && r.height < 44; })"
        ".map(el => el.outerHTML.slice(0, 80))"
    )
    assert small == []
