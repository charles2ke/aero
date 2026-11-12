"""Checks for generated and static website files that need no browser."""

from __future__ import annotations

import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
WEBSITE = ROOT / "website"
SITE_URL = "https://charles2ke.github.io/aero/"


def test_api_reference_matches_the_package():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_api_reference.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_sitemap_lists_the_published_page():
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    root = ET.parse(WEBSITE / "sitemap.xml").getroot()
    assert [loc.text for loc in root.findall("sm:url/sm:loc", namespace)] == [SITE_URL]


def test_opensearch_uses_the_page_search_parameter():
    namespace = {"os": "http://a9.com/-/spec/opensearch/1.1/"}
    root = ET.parse(WEBSITE / "opensearch.xml").getroot()
    url = root.find("os:Url[@type='text/html']", namespace)
    assert url.get("template") == SITE_URL + "?q={searchTerms}"
