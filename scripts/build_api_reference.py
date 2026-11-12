#!/usr/bin/env python3
"""Regenerate the API reference embedded in ``website/index.html``.

The reference lists every public function and client method in the
``aero`` package, with signatures and docstring summaries read from the
source, so the website and its search index stay in sync with the code.

Usage::

    python scripts/build_api_reference.py          # rewrite website/index.html
    python scripts/build_api_reference.py --check  # exit 1 if it is out of date
"""

from __future__ import annotations

import argparse
import html
import importlib
import inspect
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
INDEX = ROOT / "website" / "index.html"
START = "<!-- api-reference:start -->"
END = "<!-- api-reference:end -->"
INDENT = "      "

# (module, blurb, sprite icon) in the order they appear on the page.
MODULES = [
    ("atmosphere", "International Standard Atmosphere (ISA) from sea level to 20 km.", "cloud"),
    ("aerodynamics", "Dynamic pressure, lift, drag, Mach and Reynolds numbers.", "wing"),
    ("orbital", "Two-body orbital velocity, period and escape velocity.", "orbit"),
    ("rocketry", "Rocket equation, propellant sizing, thrust and staging.", "rocket"),
    ("navigation", "Great-circle distance, bearings and waypoints.", "compass"),
    ("nasa", "NASA Open APIs, APOD, EONET, the Image Library, TechPort and the Exoplanet Archive.", "planet"),
    ("esa", "Copernicus Sentinel products, the Gaia Archive and NEOCC near-Earth object data.", "satellite"),
    ("iss", "ISS state vectors, TLEs, CelesTrak elements and Open Notify crew data.", "station"),
    ("isro", "ISRO catalogues, Launch Library 2 launches and NavIC elements.", "globe"),
]

# Status badges for entries whose upstream service changed recently.
TAGS = {
    "nasa.apod": ("updated", "Updated"),
    "nasa.mars_rover_photos": ("deprecated", "Deprecated"),
    "nasa.eonet_events": ("new", "New"),
    "nasa.image_search": ("new", "New"),
    "nasa.insight_weather": ("archival", "Archival"),
    "nasa.techport_projects": ("updated", "Updated"),
    "nasa.techport_project": ("updated", "Updated"),
    "esa.open_data_search": ("deprecated", "Deprecated"),
    "esa.open_data_dataset": ("deprecated", "Deprecated"),
    "esa.neocc_risk_list": ("updated", "Updated"),
    "esa.neocc_query": ("new", "New"),
    "iss.current_location": ("http", "HTTP only"),
    "iss.people_in_space": ("http", "HTTP only"),
    "isro.launches": ("updated", "Updated"),
    "isro.agency": ("updated", "Updated"),
}


def _signature(fn, drop_self=False):
    sig = inspect.signature(fn)
    params = []
    for param in sig.parameters.values():
        if drop_self and param.name == "self":
            continue
        text = param.name
        annotated = param.annotation is not inspect.Parameter.empty
        if annotated:
            text += ": " + str(param.annotation).strip("'")
        if param.default is not inspect.Parameter.empty:
            text += (" = " if annotated else "=") + repr(param.default)
        params.append(text)
    returns = ""
    if sig.return_annotation is not inspect.Signature.empty:
        returns = " -> " + str(sig.return_annotation).strip("'")
    return f"({', '.join(params)}){returns}"


def _summary(obj):
    doc = inspect.getdoc(obj) or ""
    text = doc.split("\n\n")[0].replace("\n", " ").strip()
    text = re.sub(r":(meth|class|data|func):`~?([^`]+)`", r"\2", text)
    return text.replace("``", "")


def public_entries(module):
    """Return the client class (if any) and ``(name, signature, summary)`` rows.

    Calculation modules expose functions; data modules expose one client
    class whose public methods are listed instead. Exceptions are skipped.
    """
    entries = []
    client = None
    for name, obj in vars(module).items():
        if name.startswith("_") or getattr(obj, "__module__", None) != module.__name__:
            continue
        if inspect.isfunction(obj):
            entries.append((name, _signature(obj), _summary(obj)))
        elif inspect.isclass(obj) and not issubclass(obj, Exception):
            client = obj
            for method_name, method in vars(obj).items():
                if method_name.startswith("_") or not inspect.isfunction(method):
                    continue
                entries.append((method_name, _signature(method, True), _summary(method)))
    return client, entries


def render():
    lines = []
    for name, blurb, icon in MODULES:
        module = importlib.import_module("aero." + name)
        client, entries = public_entries(module)
        errors = [
            n for n, o in vars(module).items()
            if inspect.isclass(o) and issubclass(o, Exception) and o.__module__ == module.__name__
        ]
        noun = "method" if client else "function"
        count = f"{len(entries)} {noun}{'' if len(entries) == 1 else 's'}"
        lines += [
            f'<article class="api-module" id="api-{name}" aria-labelledby="api-{name}-heading">',
            '  <div class="api-module-head">',
            '    <span class="icon-badge"><svg class="icon" aria-hidden="true" focusable="false">'
            f'<use href="#icon-{icon}"></use></svg></span>',
            f'    <h3 id="api-{name}-heading"><code>aero.{name}</code></h3>',
            f'    <p class="api-blurb">{html.escape(blurb)}</p>',
        ]
        if client:
            init = _signature(client.__init__, True).split(" -> ")[0]
            raises = f' raises <code>{errors[0]}</code>' if errors else ""
            lines.append(
                f'    <p class="api-client"><code>{client.__name__}{html.escape(init)}</code>{raises}</p>'
            )
        lines += [
            '  </div>',
            '  <details class="api-details">',
            f'    <summary><span class="api-count">{count}</span>'
            f'<span class="sr-only"> in aero.{name}</span></summary>',
            '    <dl class="api-list">',
        ]
        for entry, signature, summary in entries:
            tag = TAGS.get(f"{name}.{entry}")
            badge = f' <span class="tag tag-{tag[0]}">{tag[1]}</span>' if tag else ""
            lines += [
                f'      <div class="api-entry" id="api-{name}-{entry}">',
                f'        <dt><code><span class="api-name">{html.escape(entry)}</span>'
                f'{html.escape(signature)}</code>{badge}</dt>',
                f'        <dd>{html.escape(summary)}</dd>',
                '      </div>',
            ]
        lines += ['    </dl>', '  </details>', '</article>']
    return "\n".join(INDENT + line for line in lines)


def splice(page, reference):
    start = page.index(START) + len(START)
    end = page.index(END)
    line_start = page.rindex("\n", 0, end) + 1
    return page[:start] + "\n" + reference + "\n" + page[line_start:]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if index.html is stale")
    args = parser.parse_args(argv)

    sys.path.insert(0, str(ROOT))
    page = INDEX.read_text(encoding="utf-8")
    updated = splice(page, render())
    if args.check:
        if updated != page:
            print("website/index.html API reference is out of date; run "
                  "python scripts/build_api_reference.py", file=sys.stderr)
            return 1
        print("API reference is up to date.")
        return 0
    INDEX.write_text(updated, encoding="utf-8")
    print(f"Wrote API reference to {INDEX.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
