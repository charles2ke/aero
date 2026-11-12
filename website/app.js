// aero website: calculators, live data explorer, search palette and visual effects.
// The calculators are a browser port of the formulas in the aero Python package.
(function () {
  "use strict";

  var reducedMotion =
    !!window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var isApple = /Mac|iPhone|iPad|iPod/.test(
    (navigator.userAgentData && navigator.userAgentData.platform) ||
      navigator.platform ||
      navigator.userAgent ||
      ""
  );

  function each(selector, callback, root) {
    Array.prototype.forEach.call((root || document).querySelectorAll(selector), callback);
  }

  // aero.atmosphere constants.
  var T0 = 288.15;
  var P0 = 101325.0;
  var G0 = 9.80665;
  var R = 287.05287;
  var GAMMA = 1.4;
  var TROPOPAUSE_ALTITUDE = 11000.0;
  var TROPOPAUSE_TEMPERATURE = 216.65;
  var LAPSE_RATE_TROPOSPHERE = -0.0065;
  var STRATOSPHERE_LIMIT_ALTITUDE = 20000.0;

  // aero.orbital constants.
  var EARTH_MU = 3.986004418e14;
  var EARTH_RADIUS = 6378137.0;

  function temperature(altitude) {
    if (altitude < 0) throw new RangeError("altitude must be non-negative");
    if (altitude <= TROPOPAUSE_ALTITUDE) {
      return T0 + LAPSE_RATE_TROPOSPHERE * altitude;
    }
    if (altitude <= STRATOSPHERE_LIMIT_ALTITUDE) return TROPOPAUSE_TEMPERATURE;
    throw new RangeError("altitude must be <= 20000 m for this model");
  }

  function pressure(altitude) {
    if (altitude < 0) throw new RangeError("altitude must be non-negative");
    if (altitude <= TROPOPAUSE_ALTITUDE) {
      var exponent = -G0 / (LAPSE_RATE_TROPOSPHERE * R);
      return P0 * Math.pow(temperature(altitude) / T0, exponent);
    }
    if (altitude <= STRATOSPHERE_LIMIT_ALTITUDE) {
      var p11 = pressure(TROPOPAUSE_ALTITUDE);
      return p11 * Math.exp(
        (-G0 * (altitude - TROPOPAUSE_ALTITUDE)) / (R * TROPOPAUSE_TEMPERATURE)
      );
    }
    throw new RangeError("altitude must be <= 20000 m for this model");
  }

  function density(altitude) {
    return pressure(altitude) / (R * temperature(altitude));
  }

  function speedOfSound(altitude) {
    return Math.sqrt(GAMMA * R * temperature(altitude));
  }

  function dynamicPressure(rho, velocity) {
    return 0.5 * rho * velocity * velocity;
  }

  function circularOrbitalVelocity(mu, radius) {
    if (radius <= 0) throw new RangeError("radius must be positive");
    return Math.sqrt(mu / radius);
  }

  function orbitalPeriod(mu, semiMajorAxis) {
    if (semiMajorAxis <= 0) throw new RangeError("semi_major_axis must be positive");
    return 2 * Math.PI * Math.sqrt(Math.pow(semiMajorAxis, 3) / mu);
  }

  function escapeVelocity(mu, radius) {
    if (radius <= 0) throw new RangeError("radius must be positive");
    return Math.sqrt((2 * mu) / radius);
  }

  // aero.rocketry constants.
  var STANDARD_GRAVITY = 9.80665;

  function exhaustVelocity(isp) {
    if (isp <= 0) throw new RangeError("specific_impulse must be positive");
    return isp * STANDARD_GRAVITY;
  }

  function massRatio(initialMass, finalMass) {
    if (initialMass <= 0 || finalMass <= 0) {
      throw new RangeError("initial_mass and final_mass must be positive");
    }
    if (finalMass > initialMass) {
      throw new RangeError("final_mass must not exceed initial_mass");
    }
    return initialMass / finalMass;
  }

  function deltaV(exhaustSpeed, initialMass, finalMass) {
    if (exhaustSpeed <= 0) throw new RangeError("exhaust_speed must be positive");
    return exhaustSpeed * Math.log(massRatio(initialMass, finalMass));
  }

  function massFlowRate(thrustForce, exhaustSpeed) {
    if (thrustForce <= 0) throw new RangeError("thrust_force must be positive");
    if (exhaustSpeed <= 0) throw new RangeError("exhaust_speed must be positive");
    return thrustForce / exhaustSpeed;
  }

  function burnTime(propellant, flowRate) {
    if (propellant < 0) throw new RangeError("propellant must not be negative");
    if (flowRate <= 0) throw new RangeError("flow_rate must be positive");
    return propellant / flowRate;
  }

  function thrustToWeightRatio(thrustForce, mass) {
    if (thrustForce < 0) throw new RangeError("thrust_force must not be negative");
    if (mass <= 0) throw new RangeError("mass must be positive");
    return thrustForce / (mass * STANDARD_GRAVITY);
  }

  // aero.navigation constants (IUGG mean Earth radius R1).
  var EARTH_MEAN_RADIUS = 6371008.8;

  function validatePosition(latitude, longitude) {
    if (!(latitude >= -90 && latitude <= 90)) {
      throw new RangeError("latitude must be between -90 and 90 degrees");
    }
    if (!(longitude >= -180 && longitude <= 360)) {
      throw new RangeError("longitude must be between -180 and 360 degrees");
    }
  }

  function centralAngle(lat1, lon1, lat2, lon2) {
    validatePosition(lat1, lon1);
    validatePosition(lat2, lon2);
    var phi1 = (lat1 * Math.PI) / 180;
    var phi2 = (lat2 * Math.PI) / 180;
    var deltaPhi = phi2 - phi1;
    var deltaLambda = ((lon2 - lon1) * Math.PI) / 180;
    var a =
      Math.pow(Math.sin(deltaPhi / 2), 2) +
      Math.cos(phi1) * Math.cos(phi2) * Math.pow(Math.sin(deltaLambda / 2), 2);
    a = Math.min(1, Math.max(0, a));
    return 2 * Math.asin(Math.sqrt(a));
  }

  function greatCircleDistance(lat1, lon1, lat2, lon2) {
    return EARTH_MEAN_RADIUS * centralAngle(lat1, lon1, lat2, lon2);
  }

  function initialBearing(lat1, lon1, lat2, lon2) {
    validatePosition(lat1, lon1);
    validatePosition(lat2, lon2);
    var phi1 = (lat1 * Math.PI) / 180;
    var phi2 = (lat2 * Math.PI) / 180;
    var deltaLambda = ((lon2 - lon1) * Math.PI) / 180;
    var y = Math.sin(deltaLambda) * Math.cos(phi2);
    var x =
      Math.cos(phi1) * Math.sin(phi2) -
      Math.sin(phi1) * Math.cos(phi2) * Math.cos(deltaLambda);
    return (((Math.atan2(y, x) * 180) / Math.PI) % 360 + 360) % 360;
  }

  function finalBearing(lat1, lon1, lat2, lon2) {
    return (initialBearing(lat2, lon2, lat1, lon1) + 180) % 360;
  }

  function intermediatePoint(lat1, lon1, lat2, lon2, fraction) {
    if (!(fraction >= 0 && fraction <= 1)) {
      throw new RangeError("fraction must be between 0 and 1");
    }
    var delta = centralAngle(lat1, lon1, lat2, lon2);
    var phi1 = (lat1 * Math.PI) / 180;
    var lambda1 = (lon1 * Math.PI) / 180;
    var phi2 = (lat2 * Math.PI) / 180;
    var lambda2 = (lon2 * Math.PI) / 180;
    if (delta === 0) return [lat1, ((lon1 + 540) % 360) - 180];
    if (Math.abs(delta - Math.PI) <= 1e-7) {
      throw new RangeError("shortest path is undefined for antipodal positions");
    }
    var a = Math.sin((1 - fraction) * delta) / Math.sin(delta);
    var b = Math.sin(fraction * delta) / Math.sin(delta);
    var x = a * Math.cos(phi1) * Math.cos(lambda1) + b * Math.cos(phi2) * Math.cos(lambda2);
    var y = a * Math.cos(phi1) * Math.sin(lambda1) + b * Math.cos(phi2) * Math.sin(lambda2);
    var z = a * Math.sin(phi1) + b * Math.sin(phi2);
    var phi = Math.atan2(z, Math.sqrt(x * x + y * y));
    var lam = Math.atan2(y, x);
    return [(phi * 180) / Math.PI, ((((lam * 180) / Math.PI) + 540) % 360) - 180];
  }

  function format(value, digits) {
    return Number(value).toFixed(digits === undefined ? 3 : digits);
  }

  function readNumber(id) {
    var element = document.getElementById(id);
    var value = parseFloat(element.value);
    if (!isFinite(value)) {
      var error = new RangeError(
        "Enter a number for “" + element.labels[0].textContent.trim() + "”"
      );
      error.input = element;
      throw error;
    }
    return value;
  }

  function clearInvalid(output) {
    var form = output.closest("form");
    if (!form) return;
    Array.prototype.forEach.call(form.elements, function (element) {
      element.removeAttribute("aria-invalid");
      element.removeAttribute("aria-describedby");
    });
  }

  function markInvalid(output, input) {
    if (!input) return;
    input.setAttribute("aria-invalid", "true");
    if (output.id) input.setAttribute("aria-describedby", output.id);
  }

  // Calculator results are shown as labelled metrics; the first one is emphasised.
  function metricElement(metric) {
    var item = document.createElement("span");
    item.className = metric.primary ? "metric is-primary" : "metric";
    var label = document.createElement("span");
    label.className = "metric-label";
    label.textContent = metric.label;
    var value = document.createElement("span");
    value.className = "metric-value";
    value.textContent = metric.value;
    if (metric.unit) {
      var unit = document.createElement("span");
      unit.className = "metric-unit";
      unit.textContent = (metric.unit.charAt(0) === "°" ? "" : " ") + metric.unit;
      value.appendChild(unit);
    }
    item.appendChild(label);
    item.appendChild(document.createTextNode(" "));
    item.appendChild(value);
    return item;
  }

  function render(outputId, compute) {
    var output = document.getElementById(outputId);
    clearInvalid(output);
    try {
      var metrics = compute();
      output.textContent = "";
      metrics.forEach(function (metric, index) {
        metric.primary = index === 0;
        output.appendChild(metricElement(metric));
      });
      output.classList.remove("error");
      output.classList.add("has-metrics");
    } catch (err) {
      output.textContent = "Error: " + err.message;
      output.classList.add("error");
      output.classList.remove("has-metrics");
      markInvalid(output, err.input);
    }
  }

  function updateAtmosphere() {
    render("atmosphere-output", function () {
      var h = readNumber("alt");
      return [
        { label: "Density", value: format(density(h), 4), unit: "kg/m³" },
        { label: "Temperature", value: format(temperature(h), 2), unit: "K" },
        { label: "Pressure", value: format(pressure(h), 1), unit: "Pa" },
        { label: "Speed of sound", value: format(speedOfSound(h), 2), unit: "m/s" }
      ];
    });
  }

  function updateAerodynamics() {
    render("aero-output", function () {
      var h = readNumber("aero-alt");
      var v = readNumber("aero-v");
      var area = readNumber("aero-area");
      var cl = readNumber("aero-cl");
      var cd = readNumber("aero-cd");
      if (v < 0) throw new RangeError("true airspeed must be non-negative");
      if (area < 0) throw new RangeError("wing area must be non-negative");
      if (cd === 0) throw new RangeError("cd must be non-zero");
      var rho = density(h);
      var q = dynamicPressure(rho, v);
      return [
        { label: "Lift", value: format(q * area * cl, 1), unit: "N" },
        { label: "Dynamic pressure", value: format(q, 1), unit: "Pa" },
        { label: "Drag", value: format(q * area * cd, 1), unit: "N" },
        { label: "L/D", value: format(cl / cd, 2) },
        { label: "Mach", value: format(v / speedOfSound(h), 3) }
      ];
    });
  }

  function updateOrbital() {
    render("orbital-output", function () {
      var altitude = readNumber("orb-alt");
      if (altitude < 0) throw new RangeError("altitude must be non-negative");
      var radius = EARTH_RADIUS + altitude * 1000;
      var period = orbitalPeriod(EARTH_MU, radius);
      return [
        {
          label: "Circular velocity",
          value: format(circularOrbitalVelocity(EARTH_MU, radius), 1),
          unit: "m/s"
        },
        { label: "Orbital radius", value: format(radius / 1000, 1), unit: "km" },
        { label: "Period", value: format(period / 60, 2), unit: "min" },
        { label: "Escape velocity", value: format(escapeVelocity(EARTH_MU, radius), 1), unit: "m/s" }
      ];
    });
  }

  function updateRocketry() {
    render("rocketry-output", function () {
      var isp = readNumber("rkt-isp");
      var m0 = readNumber("rkt-m0");
      var mf = readNumber("rkt-mf");
      var thrustForce = readNumber("rkt-thrust");
      var ve = exhaustVelocity(isp);
      var propellant = m0 - mf;
      var flow = massFlowRate(thrustForce, ve);
      return [
        { label: "Delta-v", value: format(deltaV(ve, m0, mf), 1), unit: "m/s" },
        { label: "Exhaust velocity", value: format(ve, 1), unit: "m/s" },
        { label: "Mass ratio", value: format(massRatio(m0, mf), 3) },
        { label: "Propellant mass", value: format(propellant, 1), unit: "kg" },
        { label: "Mass flow rate", value: format(flow, 2), unit: "kg/s" },
        { label: "Burn time", value: format(burnTime(propellant, flow), 1), unit: "s" },
        { label: "Thrust-to-weight", value: format(thrustToWeightRatio(thrustForce, m0), 2) }
      ];
    });
  }

  function updateNavigation() {
    render("navigation-output", function () {
      var lat1 = readNumber("nav-lat1");
      var lon1 = readNumber("nav-lon1");
      var lat2 = readNumber("nav-lat2");
      var lon2 = readNumber("nav-lon2");
      var distance = greatCircleDistance(lat1, lon1, lat2, lon2);
      var mid = intermediatePoint(lat1, lon1, lat2, lon2, 0.5);
      return [
        { label: "Distance", value: format(distance / 1000, 1), unit: "km" },
        { label: "Initial bearing", value: format(initialBearing(lat1, lon1, lat2, lon2), 1), unit: "°" },
        { label: "Final bearing", value: format(finalBearing(lat1, lon1, lat2, lon2), 1), unit: "°" },
        { label: "Midpoint", value: format(mid[0], 4) + "°, " + format(mid[1], 4) + "°" }
      ];
    });
  }

  // Range sliders mirror their number input in both directions. The slider's own
  // listener runs before the form's, so calculators always read the synced value.
  function setupSliders() {
    each("input.slider[data-sync]", function (slider) {
      var input = document.getElementById(slider.getAttribute("data-sync"));
      if (!input) return;
      function paint() {
        var min = parseFloat(slider.min) || 0;
        var max = parseFloat(slider.max) || 100;
        var percent = ((parseFloat(slider.value) - min) / (max - min)) * 100;
        slider.style.setProperty("--fill", Math.max(0, Math.min(100, percent)) + "%");
      }
      slider.addEventListener("input", function () {
        input.value = slider.value;
        paint();
      });
      input.addEventListener("input", function () {
        var value = parseFloat(input.value);
        if (isFinite(value)) {
          slider.value = String(value);
          paint();
        }
      });
      if (isFinite(parseFloat(input.value))) slider.value = input.value;
      paint();
    });
  }

  function bind(formId, handler) {
    var form = document.getElementById(formId);
    if (!form) return;
    form.addEventListener("input", handler);
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      handler();
    });
    handler();
  }

  setupSliders();
  bind("atmosphere-form", updateAtmosphere);
  bind("aero-form", updateAerodynamics);
  bind("orbital-form", updateOrbital);
  bind("rocketry-form", updateRocketry);
  bind("navigation-form", updateNavigation);

  // Adds a copy button to every code block so snippets can be copied in one click.
  function setupCopyButtons() {
    var manualHint = isApple ? "Press ⌘C" : "Press Ctrl+C";
    each("pre.code", function (block) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "copy-button";
      button.innerHTML =
        '<svg class="icon" aria-hidden="true" focusable="false">' +
        '<use href="#icon-copy"></use></svg><span class="copy-label">Copy</span>';
      var label = block.getAttribute("aria-label");
      if (label) {
        var hint = document.createElement("span");
        hint.className = "sr-only";
        hint.textContent = " " + label;
        button.appendChild(hint);
      }
      var toolbar = document.createElement("div");
      toolbar.className = "code-toolbar";
      var dots = document.createElement("span");
      dots.className = "code-dots";
      dots.setAttribute("aria-hidden", "true");
      dots.innerHTML = "<span></span><span></span><span></span>";
      toolbar.appendChild(dots);
      var code = block.querySelector("code");
      var language = code && code.classList.contains("language-shell") ? "Shell"
        : code && code.classList.contains("language-python") ? "Python" : "";
      if (language) {
        var tag = document.createElement("span");
        tag.className = "code-lang";
        tag.setAttribute("aria-hidden", "true");
        tag.textContent = language;
        toolbar.appendChild(tag);
      }
      toolbar.appendChild(button);
      var wrapper = document.createElement("div");
      wrapper.className = "code-wrapper";
      block.parentNode.insertBefore(wrapper, block);
      wrapper.appendChild(toolbar);
      wrapper.appendChild(block);

      var copyLabel = button.querySelector(".copy-label");
      var reset = null;
      function feedback(text, state) {
        copyLabel.textContent = text;
        button.classList.toggle("is-copied", state === "copied");
        button.classList.toggle("is-error", state === "error");
        window.clearTimeout(reset);
        reset = window.setTimeout(function () {
          copyLabel.textContent = "Copy";
          button.classList.remove("is-copied", "is-error");
        }, 2000);
      }

      button.addEventListener("click", function () {
        var text = block.textContent;
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(
            function () {
              feedback("Copied", "copied");
            },
            function () {
              feedback(manualHint, "error");
            }
          );
          return;
        }
        feedback(manualHint, "error");
      });
    });
  }

  setupCopyButtons();

  // ---------------------------------------------------------------------------
  // Data explorer: an endpoint catalogue mirroring the Python data-service clients.

  function isoDate(offsetDays) {
    return new Date(Date.now() + (offsetDays || 0) * 86400000).toISOString().slice(0, 10);
  }

  function pyNum(value) {
    var text = String(value).trim();
    return text !== "" && isFinite(Number(text)) ? String(Number(text)) : pyStr(value);
  }

  // Decodes HTML entities in API titles without ever inserting markup into the page.
  function plainText(value) {
    if (value && typeof value === "object") value = value.rendered;
    if (typeof value !== "string" || !value) return "";
    if (!/[&<]/.test(value)) return value;
    return new DOMParser().parseFromString(value, "text/html").documentElement.textContent;
  }

  var TODAY = isoDate(0);
  var NOW = Math.floor(Date.now() / 1000);
  var API_KEY_PARAM = { label: "API key", value: "DEMO_KEY", query: "api_key" };
  var TECHPORT_NOTE =
    "TechPort may ask for an API token. The Python client sends techport_token " +
    "(or TECHPORT_API_TOKEN) as a Bearer header; this browser request has none.";
  var LL2_NOTE =
    "Launch Library 2 limits anonymous clients to a small hourly request quota; " +
    "an API key from The Space Devs raises it.";

  var DOCS = {
    nasa: "https://api.nasa.gov/",
    apod: "https://github.com/nasa/api-docs/blob/gh-pages/assets/files/apod/APOD-APIs-and-RSS-info.pdf",
    images: "https://images.nasa.gov/docs/images.nasa.gov_api_docs.pdf",
    eonet: "https://eonet.gsfc.nasa.gov/docs/v3",
    techport: "https://techport.nasa.gov/help/articles/api",
    exoplanets: "https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html",
    marsPhotos: "https://github.com/corincerami/mars-photo-api",
    copernicus: "https://documentation.dataspace.copernicus.eu/APIs/OData.html",
    gaia: "https://www.cosmos.esa.int/web/gaia-users/archive/programmatic-access",
    neocc: "https://neo.ssa.esa.int/computer-access",
    whereTheIss: "https://wheretheiss.at/w/developer",
    openNotify: "https://github.com/open-notify/Open-Notify-API",
    celestrak: "https://celestrak.org/NORAD/documentation/gp-data-formats.php",
    isroApi: "https://github.com/isro/api",
    ll2: "https://github.com/TheSpaceDevs/Tutorials/blob/main/faqs/faq_LL2.md"
  };

  var TAG_LABELS = {
    "new": "New",
    updated: "Updated",
    changed: "Changed",
    key: "API key",
    nokey: "No key",
    token: "Token",
    http: "HTTP only",
    rate: "Rate-limited",
    retired: "Retired",
    archival: "Archival",
    text: "Plain text",
    community: "Community",
    agency: "Agency"
  };

  function firstEntry(data) {
    return Array.isArray(data) ? data[0] : data;
  }

  var ENDPOINTS = {
    nasa: [
      {
        label: "neo_feed() — near-Earth objects passing today",
        snippet: "nasa.NASAClient().neo_feed(start_date=" + pyStr(TODAY) + ", end_date=" + pyStr(TODAY) + ")",
        url: "https://api.nasa.gov/neo/rest/v1/feed",
        query: { start_date: TODAY, end_date: TODAY },
        param: API_KEY_PARAM,
        tags: ["key", "agency"],
        docs: DOCS.nasa
      },
      {
        label: "neo_lookup() — near-Earth object lookup",
        snippet: function (value) {
          return "nasa.NASAClient().neo_lookup(asteroid_id=" + pyStr(value) + ")";
        },
        url: "https://api.nasa.gov/neo/rest/v1/neo/{ASTEROID_ID}",
        query: { api_key: "DEMO_KEY" },
        param: { label: "Asteroid ID", value: "3542519", token: "{ASTEROID_ID}" },
        tags: ["key", "agency"],
        docs: DOCS.nasa
      },
      {
        label: "apod() — Astronomy Picture of the Day",
        snippet: "nasa.NASAClient().apod()",
        url: "https://science.nasa.gov/wp-json/wp/v2/apod-basic",
        query: { page: "1", per_page: "1" },
        tags: ["changed", "nokey"],
        note:
          "APOD is now served by NASA Science without an API key. In each entry, hdurl " +
          "is the image and url is the APOD post page.",
        docs: DOCS.apod,
        media: function (data) {
          var entry = firstEntry(data);
          return entry && {
            src: entry.hdurl,
            caption: plainText(entry.title) + (entry.date ? " · " + entry.date : "")
          };
        }
      },
      {
        label: "image_search() — NASA Image and Video Library",
        snippet: function (value) {
          return "nasa.NASAClient().image_search(query=" + pyStr(value) + ", media_type=\"image\")";
        },
        url: "https://images-api.nasa.gov/search",
        query: { media_type: "image" },
        param: { label: "Search terms", value: "artemis", query: "q" },
        tags: ["new", "nokey"],
        docs: DOCS.images,
        media: function (data) {
          var items = (data && data.collection && data.collection.items) || [];
          for (var i = 0; i < items.length; i += 1) {
            var links = (items[i].links || []).filter(function (link) {
              return link.render === "image" || /\.(jpe?g|png)$/i.test(link.href || "");
            });
            if (links.length) {
              return { src: links[0].href, caption: plainText(((items[i].data || [])[0] || {}).title) };
            }
          }
          return null;
        }
      },
      {
        label: "eonet_events() — open natural events (EONET)",
        snippet: function (value) {
          return "nasa.NASAClient().eonet_events(limit=" + pyNum(value) + ")";
        },
        url: "https://eonet.gsfc.nasa.gov/api/v3/events",
        query: { status: "open" },
        param: { label: "Limit", value: "5", query: "limit" },
        tags: ["new", "nokey"],
        docs: DOCS.eonet
      },
      {
        label: "donki_notifications() — DONKI space weather notifications",
        snippet: function (value) {
          return "nasa.NASAClient().donki_notifications(notification_type=" + pyStr(value) + ")";
        },
        url: "https://api.nasa.gov/DONKI/notifications",
        query: { api_key: "DEMO_KEY" },
        param: { label: "Notification type", value: "all", query: "type" },
        tags: ["key", "agency"],
        docs: DOCS.nasa
      },
      {
        label: "epic_natural_images() — EPIC full-disc Earth images",
        snippet: "nasa.NASAClient().epic_natural_images()",
        url: "https://api.nasa.gov/EPIC/api/natural",
        query: { api_key: "DEMO_KEY" },
        tags: ["key", "agency"],
        docs: DOCS.nasa,
        media: function (data) {
          var entry = Array.isArray(data) ? data[0] : null;
          var day = entry && /^(\d{4})-(\d{2})-(\d{2})/.exec(entry.date || "");
          if (!day || !/^[\w-]+$/.test(entry.image || "")) return null;
          return {
            src: "https://epic.gsfc.nasa.gov/archive/natural/" + day[1] + "/" + day[2] + "/" +
              day[3] + "/jpg/" + entry.image + ".jpg",
            caption: "DSCOVR EPIC · " + entry.date + " UTC"
          };
        }
      },
      {
        label: "exoplanets() — NASA Exoplanet Archive (ADQL)",
        snippet: function (value) {
          return "nasa.NASAClient().exoplanets(query=" + pyStr(value) + ")";
        },
        url: "https://exoplanetarchive.ipac.caltech.edu/TAP/sync",
        query: { format: "json" },
        param: {
          label: "ADQL query",
          value: "select top 5 pl_name, hostname, disc_year from ps",
          query: "query"
        },
        tags: ["nokey"],
        docs: DOCS.exoplanets
      },
      {
        label: "techport_projects() — TechPort projects updated recently",
        snippet: function (value) {
          return "nasa.NASAClient().techport_projects(updated_since=" + pyStr(value) + ")";
        },
        url: "https://techport.nasa.gov/api/projects",
        param: { label: "Updated since (YYYY-MM-DD)", value: isoDate(-30), query: "updatedSince" },
        tags: ["changed", "token"],
        note: TECHPORT_NOTE,
        docs: DOCS.techport
      },
      {
        label: "techport_project() — TechPort project detail",
        snippet: function (value) {
          return "nasa.NASAClient().techport_project(project_id=" + pyNum(value) + ")";
        },
        url: "https://techport.nasa.gov/api/projects/{PROJECT_ID}",
        param: { label: "Project ID", value: "14700", token: "{PROJECT_ID}" },
        tags: ["changed", "token"],
        note: TECHPORT_NOTE,
        docs: DOCS.techport
      },
      {
        label: "insight_weather() — InSight Mars weather (archival)",
        snippet: "nasa.NASAClient().insight_weather()",
        url: "https://api.nasa.gov/insight_weather/",
        query: { feedtype: "json", ver: "1.0", api_key: "DEMO_KEY" },
        tags: ["archival", "key"],
        note: "Archival feed: NASA last updated it in 2021 and the InSight mission ended in December 2022.",
        docs: DOCS.nasa
      },
      {
        label: "mars_rover_photos() — retired Mars Rover Photos API",
        snippet: "nasa.NASAClient().mars_rover_photos(rover=\"curiosity\", sol=1000)  # deprecated",
        url: "https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos",
        query: { sol: "1000", api_key: "DEMO_KEY" },
        tags: ["retired"],
        note:
          "NASA has retired this API and removed it from api.nasa.gov, so expect the request " +
          "to fail. The method now raises a DeprecationWarning; use image_search() for rover imagery.",
        docs: DOCS.marsPhotos
      }
    ],
    esa: [
      {
        label: "copernicus_products() — latest Copernicus Sentinel products",
        snippet: function (value) {
          return "esa.ESAClient().copernicus_products(collection=" + pyStr(value) +
            ", top=5, orderby=\"ContentDate/Start desc\")";
        },
        url: "https://catalogue.dataspace.copernicus.eu/odata/v1/Products",
        query: { $top: "5", $orderby: "ContentDate/Start desc" },
        param: {
          label: "Collection",
          value: "SENTINEL-2",
          build: function (value) {
            return String(value).trim()
              ? { $filter: "Collection/Name eq '" + String(value).trim() + "'" }
              : {};
          }
        },
        tags: ["new", "nokey", "agency"],
        docs: DOCS.copernicus
      },
      {
        label: "gaia_query() — Gaia DR3 star catalogue (ADQL)",
        snippet: function (value) {
          return "esa.ESAClient().gaia_query(query=" + pyStr(value) + ")";
        },
        url: "https://gea.esac.esa.int/tap-server/tap/sync",
        query: { REQUEST: "doQuery", LANG: "ADQL", FORMAT: "json" },
        param: {
          label: "ADQL query",
          value: "select top 5 source_id, ra, dec, phot_g_mean_mag from gaiadr3.gaia_source",
          query: "QUERY"
        },
        tags: ["nokey", "agency"],
        note: "Gaia DR4 is scheduled for 2 December 2026; until then gaiadr3 is the current release.",
        docs: DOCS.gaia
      },
      {
        label: "neocc_risk_list() — ESA near-Earth object risk list",
        snippet: "esa.ESAClient().neocc_risk_list()",
        url: "https://neo.ssa.esa.int/PSDB-portlet/download",
        query: { file: "esa_risk_list" },
        tags: ["new", "text", "agency"],
        note: "Pipe-delimited plain text, refreshed daily by ESA's Near-Earth Object Coordination Centre.",
        docs: DOCS.neocc
      },
      {
        label: "neocc_query() — NEOCC TAP service (ADQL)",
        snippet: function (value) {
          return "esa.ESAClient().neocc_query(query=" + pyStr(value) + ")";
        },
        url: "https://dachs.neo.s2p.esa.int/tap/sync",
        query: { REQUEST: "doQuery", LANG: "ADQL", FORMAT: "json" },
        param: {
          label: "ADQL query",
          value: "SELECT table_name, description FROM TAP_SCHEMA.tables",
          query: "QUERY"
        },
        tags: ["new", "agency"],
        docs: DOCS.neocc
      }
    ],
    iss: [
      {
        label: "satellite_position() — live ISS position, altitude and speed",
        snippet: function (value) {
          return "iss.ISSClient().satellite_position(norad_id=" + pyNum(value) + ")";
        },
        url: "https://api.wheretheiss.at/v1/satellites/{NORAD_ID}",
        param: { label: "NORAD catalogue ID", value: "25544", token: "{NORAD_ID}" },
        tags: ["new", "community", "nokey"],
        docs: DOCS.whereTheIss
      },
      {
        label: "satellite_positions() — ISS positions over the next 30 minutes",
        snippet: function (value) {
          var stamps = String(value).split(",").map(function (stamp) {
            return pyNum(stamp.trim());
          });
          return "iss.ISSClient().satellite_positions(timestamps=[" + stamps.join(", ") + "])";
        },
        url: "https://api.wheretheiss.at/v1/satellites/25544/positions",
        param: {
          label: "Unix timestamps (comma-separated, up to 10)",
          value: [NOW, NOW + 900, NOW + 1800].join(","),
          query: "timestamps"
        },
        tags: ["new", "community", "nokey"],
        docs: DOCS.whereTheIss
      },
      {
        label: "tle() — latest ISS two-line element set",
        snippet: "iss.ISSClient().tle()",
        url: "https://api.wheretheiss.at/v1/satellites/25544/tles",
        tags: ["new", "community", "nokey"],
        docs: DOCS.whereTheIss
      },
      {
        label: "celestrak_elements() — CelesTrak orbital elements (OMM)",
        snippet: function (value) {
          return "iss.ISSClient().celestrak_elements(group=" + pyStr(value) + ")";
        },
        url: "https://celestrak.org/NORAD/elements/gp.php",
        query: { FORMAT: "json" },
        param: { label: "CelesTrak group", value: "stations", query: "GROUP" },
        tags: ["new", "nokey"],
        docs: DOCS.celestrak
      },
      {
        label: "people_in_space() — people in orbit right now",
        snippet: "iss.ISSClient().people_in_space()",
        url: "http://api.open-notify.org/astros.json",
        tags: ["http", "community"],
        note:
          "Open Notify serves plain HTTP only and its crew list is maintained by hand, so it can " +
          "lag behind crew rotations.",
        docs: DOCS.openNotify
      },
      {
        label: "current_location() — ISS latitude and longitude (Open Notify)",
        snippet: "iss.ISSClient().current_location()",
        url: "http://api.open-notify.org/iss-now.json",
        tags: ["http", "community"],
        note:
          "Plain HTTP only and no longer actively maintained; satellite_position() is the HTTPS " +
          "alternative and adds altitude and velocity.",
        docs: DOCS.openNotify
      }
    ],
    isro: [
      {
        label: "spacecrafts() — ISRO spacecraft catalogue",
        snippet: "isro.ISROClient().spacecrafts()",
        url: "https://isro.vercel.app/api/spacecrafts",
        tags: ["community", "nokey"],
        docs: DOCS.isroApi
      },
      {
        label: "launchers() — ISRO launch vehicles",
        snippet: "isro.ISROClient().launchers()",
        url: "https://isro.vercel.app/api/launchers",
        tags: ["community", "nokey"],
        docs: DOCS.isroApi
      },
      {
        label: "customer_satellites() — customer satellites launched by ISRO",
        snippet: "isro.ISROClient().customer_satellites()",
        url: "https://isro.vercel.app/api/customer_satellites",
        tags: ["community", "nokey"],
        docs: DOCS.isroApi
      },
      {
        label: "centres() — ISRO centres and units",
        snippet: "isro.ISROClient().centres()",
        url: "https://isro.vercel.app/api/centres",
        tags: ["community", "nokey"],
        docs: DOCS.isroApi
      },
      {
        label: "launches() — recent ISRO launches (Launch Library 2)",
        snippet: function (value) {
          return "isro.ISROClient().launches(limit=" + pyNum(value) + ")";
        },
        url: "https://ll.thespacedevs.com/2.3.0/launches/previous/",
        query: { lsp__id: "31" },
        param: { label: "Limit", value: "5", query: "limit" },
        tags: ["updated", "rate"],
        note: LL2_NOTE,
        docs: DOCS.ll2
      },
      {
        label: "launches(upcoming=True) — upcoming ISRO launches",
        snippet: function (value) {
          return "isro.ISROClient().launches(upcoming=True, limit=" + pyNum(value) + ")";
        },
        url: "https://ll.thespacedevs.com/2.3.0/launches/upcoming/",
        query: { lsp__id: "31" },
        param: { label: "Limit", value: "5", query: "limit" },
        tags: ["updated", "rate"],
        note: LL2_NOTE,
        docs: DOCS.ll2
      },
      {
        label: "agency() — ISRO agency profile (Launch Library 2)",
        snippet: "isro.ISROClient().agency()",
        url: "https://ll.thespacedevs.com/2.3.0/agencies/31/",
        tags: ["updated", "rate"],
        note: LL2_NOTE,
        docs: DOCS.ll2
      },
      {
        label: "navic_elements() — NavIC (IRNSS) orbital elements",
        snippet: "isro.ISROClient().navic_elements()",
        url: "https://celestrak.org/NORAD/elements/gp.php",
        query: { FORMAT: "json", NAME: "IRNSS" },
        tags: ["nokey"],
        docs: DOCS.celestrak
      },
      {
        label: "celestrak_elements() — CelesTrak group elements",
        snippet: function (value) {
          return "isro.ISROClient().celestrak_elements(group=" + pyStr(value) + ")";
        },
        url: "https://celestrak.org/NORAD/elements/gp.php",
        query: { FORMAT: "json" },
        param: { label: "CelesTrak group", value: "gnss", query: "GROUP" },
        tags: ["nokey"],
        docs: DOCS.celestrak
      }
    ]
  };

  function buildUrl(endpoint, paramValue) {
    var rawUrl = endpoint.url;
    if (endpoint.param && endpoint.param.token) {
      var tokenValue = paramValue || endpoint.param.value;
      rawUrl = rawUrl.replace(endpoint.param.token, encodeURIComponent(tokenValue));
    }
    var url = new URL(rawUrl);
    var query = endpoint.query || {};
    Object.keys(query).forEach(function (key) {
      url.searchParams.set(key, query[key]);
    });
    if (endpoint.param && !endpoint.param.token && paramValue !== undefined && paramValue !== null) {
      var extra = endpoint.param.build
        ? endpoint.param.build(paramValue)
        : (function () {
            var single = {};
            single[endpoint.param.query] = paramValue;
            return single;
          })();
      Object.keys(extra).forEach(function (key) {
        url.searchParams.set(key, extra[key]);
      });
    }
    return url.toString();
  }

  function pyStr(value) {
    return "\"" + String(value).replace(/\\/g, "\\\\").replace(/"/g, "\\\"") + "\"";
  }

  // Some services do not send CORS headers, so a direct browser request fails even
  // though the Python client works. Such a request can be retried through a public
  // read-only proxy, but only when the visitor explicitly asks for it: the retry
  // sends the whole URL, including any query the visitor typed, to a third party.
  // The opt-in is never offered when the URL carries a private key.
  var CORS_PROXY = "https://api.allorigins.win/raw?url=";
  var SECRET_QUERY_KEYS = ["api_key", "apikey", "key", "token", "access_token"];
  var PUBLIC_KEY_VALUES = ["DEMO_KEY", ""];

  function carriesPrivateKey(url) {
    var params = new URL(url).searchParams;
    return SECRET_QUERY_KEYS.some(function (name) {
      var value = params.get(name);
      return value !== null && PUBLIC_KEY_VALUES.indexOf(value) === -1;
    });
  }

  function proxyUrl(url) {
    return CORS_PROXY + encodeURIComponent(url);
  }

  function preview(text, limit) {
    var max = limit === undefined ? 1200 : limit;
    return text.length > max ? text.slice(0, max) + "\n… truncated" : text;
  }

  // Splits pretty-printed JSON into tokens so each value can be coloured. Nodes are
  // created with textContent only, so response data is never parsed as HTML.
  var JSON_TOKEN = /("(\\.|[^"\\])*"\s*:)|("(\\.|[^"\\])*")|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)|\b(true|false|null)\b/g;

  function tokenClass(match) {
    if (/^"/.test(match)) return /:\s*$/.test(match) ? "json-key" : "json-string";
    if (match === "true" || match === "false") return "json-boolean";
    if (match === "null") return "json-null";
    return "json-number";
  }

  function highlightJSON(text) {
    var fragment = document.createDocumentFragment();
    var index = 0;
    var match;
    JSON_TOKEN.lastIndex = 0;
    while ((match = JSON_TOKEN.exec(text)) !== null) {
      if (match.index > index) {
        fragment.appendChild(document.createTextNode(text.slice(index, match.index)));
      }
      var span = document.createElement("span");
      span.className = tokenClass(match[0]);
      span.textContent = match[0];
      fragment.appendChild(span);
      index = match.index + match[0].length;
    }
    if (index < text.length) {
      fragment.appendChild(document.createTextNode(text.slice(index)));
    }
    return fragment;
  }

  // Renders a response body: pretty-printed and highlighted when it is JSON,
  // plain text otherwise, with an optional note above it.
  function renderBody(output, body, note) {
    var formatted = null;
    try {
      formatted = JSON.stringify(JSON.parse(body), null, 2);
    } catch (err) {
      /* not JSON: show the raw body */
    }
    output.textContent = "";
    output.classList.toggle("is-json", formatted !== null);
    if (note) {
      var noteElement = document.createElement("p");
      noteElement.className = "output-note";
      noteElement.textContent = note;
      output.appendChild(noteElement);
    }
    var pre = document.createElement("pre");
    pre.className = "output-body";
    if (formatted === null) {
      pre.textContent = preview(body);
    } else {
      pre.appendChild(highlightJSON(preview(formatted)));
    }
    output.appendChild(pre);
  }

  // Syntax highlighting builds DOM nodes with textContent, so typed values and
  // snippets are never interpreted as HTML.
  var PYTHON_TOKEN = new RegExp(
    [
      "(#[^\\n]*)",
      "(\"(?:\\\\.|[^\"\\\\\\n])*\"|'(?:\\\\.|[^'\\\\\\n])*')",
      "\\b(from|import|as|def|return|for|in|if|elif|else|None|True|False|with|lambda|and|or|not)\\b",
      "\\b(\\d[\\d_]*(?:\\.\\d+)?(?:[eE][+-]?\\d+)?)\\b",
      "([A-Za-z_]\\w*)(?=\\()"
    ].join("|"),
    "g"
  );
  var SHELL_TOKEN = /(#[^\n]*)|("[^"\n]*"|'[^'\n]*')|(^|\n)([\w.-]+)|(\s--?[\w-]+)/g;
  var TOKEN_CLASSES = ["tok-comment", "tok-string", "tok-keyword", "tok-number", "tok-func"];

  function appendToken(fragment, text, className) {
    if (!text) return;
    if (!className) {
      fragment.appendChild(document.createTextNode(text));
      return;
    }
    var span = document.createElement("span");
    span.className = className;
    span.textContent = text;
    fragment.appendChild(span);
  }

  function highlightPythonText(text) {
    var fragment = document.createDocumentFragment();
    var index = 0;
    var match;
    PYTHON_TOKEN.lastIndex = 0;
    while ((match = PYTHON_TOKEN.exec(text)) !== null) {
      appendToken(fragment, text.slice(index, match.index));
      for (var group = 1; group <= 5; group += 1) {
        if (match[group] !== undefined) {
          appendToken(fragment, match[0], TOKEN_CLASSES[group - 1]);
          break;
        }
      }
      index = match.index + match[0].length;
    }
    appendToken(fragment, text.slice(index));
    return fragment;
  }

  function highlightShellText(text) {
    var fragment = document.createDocumentFragment();
    var index = 0;
    var match;
    SHELL_TOKEN.lastIndex = 0;
    while ((match = SHELL_TOKEN.exec(text)) !== null) {
      appendToken(fragment, text.slice(index, match.index));
      if (match[1] !== undefined) appendToken(fragment, match[1], "tok-comment");
      else if (match[2] !== undefined) appendToken(fragment, match[2], "tok-string");
      else if (match[4] !== undefined) {
        appendToken(fragment, match[3]);
        appendToken(fragment, match[4], "tok-func");
      } else appendToken(fragment, match[5], "tok-keyword");
      index = match.index + match[0].length;
    }
    appendToken(fragment, text.slice(index));
    return fragment;
  }

  function highlightCode(element, text) {
    var source = text === undefined ? element.textContent : text;
    var shell = element.classList.contains("language-shell");
    element.textContent = "";
    element.appendChild(shell ? highlightShellText(source) : highlightPythonText(source));
  }

  each("pre.code code.language-python, pre.code code.language-shell", function (code) {
    if (!code.classList.contains("explorer-snippet")) highlightCode(code);
  });

  // Wraps a long call one argument per line, the way black formats Python,
  // so explorer snippets read without horizontal scrolling.
  var SNIPPET_WIDTH = 52;
  function formatCall(call) {
    if (call.length <= SNIPPET_WIDTH) return call;
    var stack = [];
    var quote = "";
    var open = -1;
    var close = -1;
    var commas = [];
    for (var i = 0; i < call.length; i += 1) {
      var ch = call.charAt(i);
      if (quote) {
        if (ch === "\\") i += 1;
        else if (ch === quote) quote = "";
      } else if (ch === '"' || ch === "'") {
        quote = ch;
      } else if (ch === "#") {
        break;
      } else if (ch === "(" || ch === "[" || ch === "{") {
        if (!stack.length && ch === "(") {
          open = i;
          close = -1;
          commas = [];
        }
        stack.push(ch);
      } else if (ch === ")" || ch === "]" || ch === "}") {
        stack.pop();
        if (!stack.length && ch === ")") close = i;
      } else if (ch === "," && stack.length === 1 && stack[0] === "(") {
        commas.push(i);
      }
    }
    if (open < 0 || close < open) return call;
    var args = [];
    var start = open + 1;
    commas.concat(close).forEach(function (end) {
      var arg = call.slice(start, end).trim();
      if (arg) args.push(arg);
      start = end + 1;
    });
    if (!args.length) return call;
    return call.slice(0, open + 1) + "\n" +
      args.map(function (arg) { return "    " + arg + ","; }).join("\n") +
      "\n)" + call.slice(close + 1);
  }

  function renderTags(container, tags) {
    container.textContent = "";
    (tags || []).forEach(function (tag) {
      var span = document.createElement("span");
      span.className = "tag tag-" + tag;
      span.textContent = TAG_LABELS[tag] || tag;
      container.appendChild(span);
    });
  }

  // Only https images on nasa.gov hosts are shown next to a response.
  function nasaImageUrl(src) {
    if (typeof src !== "string" || !src) return null;
    try {
      var url = new URL(src.replace(/^http:\/\//i, "https://"));
      var host = url.hostname;
      return host === "nasa.gov" || /\.nasa\.gov$/.test(host) ? url.toString() : null;
    } catch (err) {
      return null;
    }
  }

  var explorers = {};

  function setupExplorer(form) {
    var module = form.getAttribute("data-module");
    var endpoints = ENDPOINTS[module];
    if (!endpoints) return;

    var select = form.querySelector(".explorer-endpoint");
    var paramLabel = form.querySelector(".explorer-param-label");
    var paramInput = form.querySelector(".explorer-param");
    var snippet = form.querySelector(".explorer-snippet");
    var link = form.querySelector(".explorer-url");
    var output = form.querySelector(".explorer-output");
    var proxyButton = form.querySelector(".explorer-proxy");
    var sendButton = form.querySelector(".explorer-send");
    var status = form.querySelector(".explorer-status");
    var tagList = form.querySelector(".endpoint-tags");
    var note = form.querySelector(".endpoint-note");
    var docs = form.querySelector(".explorer-docs");
    var media = form.querySelector(".explorer-media");
    var mediaImage = media && media.querySelector("img");
    var mediaCaption = media && media.querySelector("figcaption");
    var latest = 0;

    endpoints.forEach(function (endpoint, index) {
      var option = document.createElement("option");
      option.value = String(index);
      option.textContent = endpoint.label;
      select.appendChild(option);
    });

    function current() {
      return endpoints[Number(select.value) || 0];
    }

    function setStatus(text, state) {
      status.textContent = text;
      status.className = "explorer-status" + (state ? " is-" + state : "");
    }

    function hideMedia() {
      if (!media) return;
      media.hidden = true;
      mediaImage.removeAttribute("src");
      mediaImage.alt = "";
      mediaCaption.textContent = "";
    }

    function showMedia(endpoint, body) {
      if (!media || !endpoint.media) return;
      var item = null;
      try {
        item = endpoint.media(JSON.parse(body));
      } catch (err) {
        item = null;
      }
      var src = item && nasaImageUrl(item.src);
      if (!src) return;
      mediaImage.onerror = hideMedia;
      mediaImage.loading = "eager";
      mediaImage.alt = item.caption || "Image returned by " + endpoint.label.split(" ")[0];
      mediaCaption.textContent = item.caption || "";
      mediaImage.src = src;
      media.hidden = false;
    }

    function refresh(endpointChanged) {
      var endpoint = current();
      if (endpoint.param) {
        paramLabel.hidden = false;
        paramLabel.firstChild.nodeValue = endpoint.param.label + " ";
        if (endpointChanged) paramInput.value = endpoint.param.value;
      } else {
        paramLabel.hidden = true;
        paramInput.value = "";
      }
      var call = typeof endpoint.snippet === "function"
        ? endpoint.snippet(paramInput.value)
        : endpoint.snippet;
      highlightCode(snippet, "from aero import " + module + "\n\n" + formatCall(call));
      var url = buildUrl(endpoint, paramInput.value);
      link.textContent = url;
      link.href = url;
      if (endpointChanged) {
        renderTags(tagList, endpoint.tags);
        note.textContent = endpoint.note || "";
        note.hidden = !endpoint.note;
        if (docs && endpoint.docs) docs.href = endpoint.docs;
        proxyButton.hidden = true;
        hideMedia();
        if (!status.classList.contains("is-loading")) setStatus("Ready");
      }
    }

    function request(url) {
      return fetch(url, { headers: { Accept: "application/json, text/plain, */*" } })
        .then(function (response) {
          return response.text().then(function (body) {
            return { ok: response.ok, status: response.status, body: body };
          });
        });
    }

    function elapsedSince(started) {
      return Math.round(window.performance.now() - started) + " ms";
    }

    function beginLoading(message) {
      output.classList.remove("error", "is-json");
      output.classList.add("loading");
      output.textContent = message;
      proxyButton.hidden = true;
      hideMedia();
      setStatus("Requesting…", "loading");
      sendButton.setAttribute("aria-busy", "true");
    }

    function showResult(result, endpoint, started, proxyNote) {
      sendButton.removeAttribute("aria-busy");
      output.classList.remove("loading");
      var timing = "HTTP " + result.status + " · " + elapsedSince(started);
      if (!result.ok) {
        output.classList.add("error");
        output.classList.remove("is-json");
        output.textContent =
          "Request failed with status " + result.status + "\n" + preview(result.body, 300);
        setStatus(timing, "error");
        return;
      }
      renderBody(output, result.body, proxyNote);
      setStatus(timing + (proxyNote ? " · via proxy" : ""), "ok");
      showMedia(endpoint, result.body);
    }

    function showFailure(err, extra) {
      sendButton.removeAttribute("aria-busy");
      output.classList.remove("loading", "is-json");
      output.classList.add("error");
      output.textContent =
        "Browser request failed (" + err.message + "). The service may block " +
        "cross-origin calls — open the URL above, or run the Python snippet." +
        (extra ? "\n" + extra : "");
      setStatus("Request failed", "error");
    }

    function send() {
      var endpoint = current();
      var url = buildUrl(endpoint, paramInput.value);
      var ticket = (latest += 1);
      var started = window.performance.now();
      beginLoading("Requesting …");
      request(url)
        .then(function (result) {
          if (ticket === latest) showResult(result, endpoint, started);
        })
        .catch(function (err) {
          if (ticket !== latest) return;
          var hints = [];
          if (/^http:/i.test(url) && window.location.protocol === "https:") {
            hints.push(
              "This endpoint only serves plain HTTP, which browsers block on HTTPS pages " +
                "(mixed content)."
            );
          }
          if (carriesPrivateKey(url)) {
            hints.push(
              "The request carries an API key, so it is not offered for a retry " +
                "through the public proxy."
            );
            showFailure(err, hints.join("\n"));
            return;
          }
          hints.push(
            "You can retry through the public read-only CORS proxy " + CORS_PROXY +
              ", which sends this URL — including the query you typed — to that " +
              "third-party service."
          );
          showFailure(err, hints.join("\n"));
          proxyButton.hidden = false;
          proxyButton.onclick = function () {
            var retryTicket = (latest += 1);
            var retryStarted = window.performance.now();
            beginLoading("Retrying through the public CORS proxy …");
            request(proxyUrl(url))
              .then(function (result) {
                if (retryTicket !== latest) return;
                showResult(
                  result,
                  endpoint,
                  retryStarted,
                  "Fetched through the public CORS proxy " + CORS_PROXY + " because " +
                    new URL(url).host + " blocks direct browser requests."
                );
              })
              .catch(function (proxyErr) {
                if (retryTicket === latest) {
                  showFailure(proxyErr, "The CORS proxy retry failed as well.");
                }
              });
          };
        });
    }

    select.addEventListener("change", function () {
      refresh(true);
    });
    paramInput.addEventListener("input", function () {
      refresh(false);
    });
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      send();
    });
    refresh(true);

    explorers[module] = {
      form: form,
      choose: function (index) {
        select.value = String(index);
        refresh(true);
      }
    };
  }

  each(".explorer", setupExplorer);

  // ---------------------------------------------------------------------------
  // Ambient visuals: starfield, card spotlight and live section highlighting.

  function setupStarfield() {
    var canvas = document.querySelector(".starfield");
    var context = canvas && canvas.getContext && canvas.getContext("2d");
    if (!context) return;

    // A seeded generator keeps the sky identical on every visit.
    var seed = 20261112;
    function random() {
      seed = (seed * 1664525 + 1013904223) % 4294967296;
      return seed / 4294967296;
    }

    var palette = ["255, 255, 255", "255, 255, 255", "255, 255, 255", "186, 230, 253", "221, 214, 254"];
    var stars = [];
    for (var i = 0; i < 260; i += 1) {
      stars.push({
        x: random(),
        y: random(),
        radius: random() * random() * 1.4 + 0.3,
        alpha: random() * 0.6 + 0.25,
        speed: random() * 0.0016 + 0.0004,
        phase: random() * Math.PI * 2,
        color: palette[Math.floor(random() * palette.length)]
      });
    }

    var width = 0;
    var height = 0;

    function draw(time) {
      context.clearRect(0, 0, width, height);
      var visible = Math.max(70, Math.round(stars.length * Math.min(1, (width * height) / (1440 * 900))));
      for (var index = 0; index < visible; index += 1) {
        var star = stars[index];
        var alpha = star.alpha;
        if (time) alpha *= 0.62 + 0.38 * Math.sin(time * star.speed + star.phase);
        context.fillStyle = "rgba(" + star.color + ", " + alpha.toFixed(3) + ")";
        context.beginPath();
        context.arc(star.x * width, star.y * height, star.radius, 0, Math.PI * 2);
        context.fill();
      }
    }

    function resize() {
      var ratio = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.round(width * ratio);
      canvas.height = Math.round(height * ratio);
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      draw(reducedMotion ? 0 : window.performance.now());
    }

    var resizePending = false;
    window.addEventListener("resize", function () {
      if (resizePending) return;
      resizePending = true;
      window.requestAnimationFrame(function () {
        resizePending = false;
        resize();
      });
    });
    resize();

    if (reducedMotion) return;
    var lastFrame = 0;
    function twinkle(time) {
      window.requestAnimationFrame(twinkle);
      if (time - lastFrame < 66) return;
      lastFrame = time;
      draw(time);
    }
    window.requestAnimationFrame(twinkle);
  }

  function setupSpotlight() {
    if (!window.matchMedia || !window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
    document.addEventListener(
      "pointermove",
      function (event) {
        if (event.pointerType !== "mouse" || !event.target.closest) return;
        var card = event.target.closest(".spotlight");
        if (!card) return;
        var rect = card.getBoundingClientRect();
        card.style.setProperty("--mx", Math.round(event.clientX - rect.left) + "px");
        card.style.setProperty("--my", Math.round(event.clientY - rect.top) + "px");
      },
      { passive: true }
    );
  }

  function setupScrollSpy() {
    if (typeof IntersectionObserver !== "function") return;
    var links = {};
    var sections = [];
    each('.nav-links a[href^="#"]', function (link) {
      var section = document.getElementById(link.getAttribute("href").slice(1));
      if (!section) return;
      links[section.id] = link;
      sections.push(section);
    });
    if (!sections.length) return;

    var currentId = null;
    function mark(id) {
      currentId = id;
      Object.keys(links).forEach(function (key) {
        if (key === id) links[key].setAttribute("aria-current", "true");
        else links[key].removeAttribute("aria-current");
      });
    }

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            mark(entry.target.id);
          } else if (entry.target.id === currentId && entry.boundingClientRect.top > 0) {
            // Scrolled back above the highlighted section, for example to the hero.
            mark(null);
          }
        });
      },
      { rootMargin: "-40% 0px -55% 0px" }
    );
    sections.forEach(function (section) {
      observer.observe(section);
    });
  }

  // ---------------------------------------------------------------------------
  // Live figures: countdowns, hero stats, ISS telemetry and module card counts.

  function setupCountdowns() {
    var now = new Date();
    var today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
    each("[data-countdown]", function (element) {
      var parts = element.getAttribute("data-countdown").split("-").map(Number);
      if (parts.length !== 3 || parts.some(isNaN)) return;
      var days = Math.round((Date.UTC(parts[0], parts[1] - 1, parts[2]) - today) / 86400000);
      element.classList.toggle("is-past", days < 0);
      if (days > 1) element.textContent = "in " + days + " days";
      else if (days === 1) element.textContent = "tomorrow";
      else if (days === 0) element.textContent = "today";
      else if (days === -1) element.textContent = "yesterday";
      else element.textContent = -days + " days ago";
    });
  }

  function countUp(element, value) {
    var started = null;
    var duration = 1100;
    element.textContent = "0";
    function step(now) {
      if (started === null) started = now;
      var progress = Math.min(1, (now - started) / duration);
      element.textContent = String(Math.round(value * (1 - Math.pow(1 - progress, 3))));
      if (progress < 1) window.requestAnimationFrame(step);
    }
    window.requestAnimationFrame(step);
  }

  function setupStats() {
    var modules = Object.keys(ENDPOINTS);
    var values = {
      calculators: document.querySelectorAll("form.calculator").length,
      clients: modules.length,
      endpoints: modules.reduce(function (total, module) {
        return total + ENDPOINTS[module].length;
      }, 0),
      functions: document.querySelectorAll(".api-entry").length
    };
    each("[data-stat]", function (element) {
      var value = values[element.getAttribute("data-stat")];
      if (!value) return;
      if (reducedMotion) element.textContent = String(value);
      else countUp(element, value);
    });
  }

  function setupTelemetry() {
    // A circular orbit at the ISS's typical 420 km altitude, using the calculator formulas.
    var radius = EARTH_RADIUS + 420000;
    var periodMinutes = orbitalPeriod(EARTH_MU, radius) / 60;
    var values = {
      velocity: (circularOrbitalVelocity(EARTH_MU, radius) / 1000).toFixed(2),
      period: periodMinutes.toFixed(2),
      orbits: (1440 / periodMinutes).toFixed(2)
    };
    each("[data-telemetry]", function (element) {
      var value = values[element.getAttribute("data-telemetry")];
      if (value) element.textContent = value;
    });
  }

  function setupCardCounts() {
    each("[data-count-for]", function (element) {
      var module = element.getAttribute("data-count-for");
      var count = document.querySelectorAll("#api-" + module + " .api-entry").length;
      if (!count) return;
      var noun = ENDPOINTS[module] ? "method" : "function";
      element.textContent = count + " " + noun + (count === 1 ? "" : "s");
    });
  }

  function setupShortcutLabels() {
    if (!isApple) return;
    each("kbd[data-shortcut]", function (element) {
      element.textContent = "\u2318 K";
    });
    each("[aria-keyshortcuts]", function (element) {
      element.setAttribute("aria-keyshortcuts", "Meta+K");
    });
  }

  // ---------------------------------------------------------------------------
  // In-page navigation: smooth anchors, deep links into the API reference and a
  // highlight ring on whatever the reader jumped to.

  var arrivingTarget = null;

  function flash(element) {
    window.clearTimeout(element.aeroFlashTimer);
    element.classList.remove("is-entering", "is-flash");
    void element.offsetWidth; // restart the animation if it is already running
    element.classList.add("is-flash");
    element.aeroFlashTimer = window.setTimeout(function () {
      element.classList.remove("is-flash");
    }, 1700);
  }

  function openAncestors(element) {
    for (var node = element; node; node = node.parentElement) {
      if (node.tagName === "DETAILS" && !node.open) node.open = true;
    }
  }

  function focusWithoutScrolling(element) {
    if (!element.hasAttribute("tabindex") && !element.matches("a[href], button, input, select, textarea, summary")) {
      element.setAttribute("tabindex", "-1");
    }
    try {
      element.focus({ preventScroll: true });
    } catch (err) {
      element.focus();
    }
  }

  // Calls back once the page has stopped scrolling (or after 1.5 s at most).
  function whenScrollSettles(callback) {
    var lastY = null;
    var stillFrames = 0;
    var started = window.performance.now();
    function check(now) {
      var y = window.pageYOffset;
      stillFrames = y === lastY ? stillFrames + 1 : 0;
      lastY = y;
      if (stillFrames >= 4 || now - started > 1500) callback();
      else window.requestAnimationFrame(check);
    }
    window.requestAnimationFrame(check);
  }

  function goTo(element, options) {
    options = options || {};
    var smooth = !reducedMotion && !options.instant;
    openAncestors(element);
    arrivingTarget = element;
    if (element.id === "top") {
      window.scrollTo({ top: 0, behavior: smooth ? "smooth" : "auto" });
    } else {
      element.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: options.block || "start" });
    }
    if (options.hash && window.history && window.history.pushState && window.location.hash !== options.hash) {
      try {
        window.history.pushState(null, "", options.hash);
      } catch (err) {
        // Some sandboxed or file:// contexts refuse history updates; navigation still works.
      }
    }
    if (options.focus !== false && element.id !== "top") focusWithoutScrolling(options.focusElement || element);
    whenScrollSettles(function () {
      if (arrivingTarget === element) arrivingTarget = null;
      if (options.flash) flash(element);
    });
  }

  function elementForHash(hash) {
    if (!hash || hash.length < 2) return null;
    var id = hash.slice(1);
    try {
      id = decodeURIComponent(id);
    } catch (err) {
      // keep the raw fragment
    }
    return document.getElementById(id);
  }

  function shouldFlash(element) {
    return element.matches(".api-entry, .api-module, .calculator, .explorer, .card, .step, .source-item");
  }

  function setupAnchors() {
    document.addEventListener("click", function (event) {
      if (event.defaultPrevented || event.button !== 0) return;
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      var link = event.target.closest && event.target.closest('a[href^="#"]');
      if (!link || link.classList.contains("skip-link")) return;
      var hash = link.getAttribute("href");
      var target = elementForHash(hash);
      if (!target) return;
      event.preventDefault();
      goTo(target, { hash: hash, flash: shouldFlash(target) });
    });

    // Fragments typed into the address bar or reached with Back/Forward may
    // point inside a collapsed API module.
    window.addEventListener("hashchange", function () {
      var target = elementForHash(window.location.hash);
      if (target && target.closest("details:not([open])")) {
        goTo(target, { instant: true, flash: shouldFlash(target) });
      }
    });
  }

  function handleInitialHash() {
    var target = elementForHash(window.location.hash);
    if (!target || target.id === "top") return;
    if (target.closest("details:not([open])") || target.matches(".api-entry")) {
      goTo(target, { instant: true, focus: false, flash: true });
    }
  }

  function setupApiToggle() {
    var toggle = document.querySelector(".api-toggle");
    var panels = document.querySelectorAll("details.api-details");
    if (!toggle || !panels.length) return;
    var label = toggle.querySelector(".api-toggle-label");

    function allOpen() {
      return Array.prototype.every.call(panels, function (panel) {
        return panel.open;
      });
    }

    function sync() {
      var open = allOpen();
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      if (label) label.textContent = open ? "Collapse all" : "Expand all";
    }

    toggle.addEventListener("click", function () {
      var open = !allOpen();
      Array.prototype.forEach.call(panels, function (panel) {
        panel.open = open;
      });
      sync();
    });
    Array.prototype.forEach.call(panels, function (panel) {
      panel.addEventListener("toggle", sync);
    });
    sync();
  }

  // ---------------------------------------------------------------------------
  // Search palette: Ctrl/⌘ K, "/" or a search button opens a finder over every
  // function, endpoint, calculator, update, source and section on the page.

  function fold(value) {
    var text = String(value || "").toLowerCase();
    return text.normalize ? text.normalize("NFD").replace(/[\u0300-\u036f]/g, "") : text;
  }

  // Folds text for matching while remembering where each character came from,
  // so highlights land on the original (accented) text.
  function searchField(value) {
    var raw = String(value || "").replace(/\s+/g, " ").trim();
    var text = "";
    var map = [];
    for (var i = 0; i < raw.length; i += 1) {
      var piece = fold(raw.charAt(i));
      for (var j = 0; j < piece.length; j += 1) {
        text += piece.charAt(j);
        map.push(i);
      }
    }
    return { raw: raw, text: text, map: map };
  }

  function queryTokens(query) {
    return fold(query)
      .split(/\s+/)
      .map(function (token) {
        return token.replace(/^[^a-z0-9]+|[^a-z0-9]+$/g, "");
      })
      .filter(Boolean);
  }

  function locate(field, token) {
    var first = field.text.indexOf(token);
    for (var at = first; at !== -1; at = field.text.indexOf(token, at + 1)) {
      if (at === 0 || !/[a-z0-9]/.test(field.text.charAt(at - 1))) return { at: at, word: true };
    }
    return first === -1 ? null : { at: first, word: false };
  }

  function scoreItem(item, tokens, phrase) {
    var total = 0;
    var marks = { title: [], subtitle: [] };
    for (var i = 0; i < tokens.length; i += 1) {
      var token = tokens[i];
      var hit = locate(item.title, token);
      if (hit) {
        if (hit.at === 0) total += item.title.text.length === token.length ? 100 : 60;
        else total += hit.word ? 40 : 20;
        marks.title.push([hit.at, hit.at + token.length]);
        continue;
      }
      hit = locate(item.subtitle, token);
      if (hit) {
        total += hit.word ? 14 : 7;
        marks.subtitle.push([hit.at, hit.at + token.length]);
        continue;
      }
      hit = locate(item.keywords, token);
      if (!hit) return null;
      total += hit.word ? 9 : 4;
    }
    if (tokens.length > 1 && item.title.text.indexOf(phrase) !== -1) total += 30;
    return { item: item, score: total + item.boost * 3, marks: marks };
  }

  function appendHighlighted(container, field, ranges) {
    var spans = ranges
      .map(function (range) {
        return [field.map[range[0]], field.map[range[1] - 1] + 1];
      })
      .sort(function (a, b) {
        return a[0] - b[0];
      });
    var cursor = 0;
    spans.forEach(function (span) {
      var start = Math.max(span[0], cursor);
      if (span[1] <= start) return;
      if (start > cursor) container.appendChild(document.createTextNode(field.raw.slice(cursor, start)));
      var mark = document.createElement("mark");
      mark.textContent = field.raw.slice(start, span[1]);
      container.appendChild(mark);
      cursor = span[1];
    });
    if (cursor < field.raw.length) container.appendChild(document.createTextNode(field.raw.slice(cursor)));
  }

  function textOf(element, skipSelector) {
    if (!element) return "";
    if (skipSelector) {
      element = element.cloneNode(true);
      each(skipSelector, function (node) {
        node.remove();
      }, element);
    }
    return element.textContent.replace(/\s+/g, " ").trim();
  }

  function buildSearchIndex() {
    var items = [];
    function add(kind, boost, title, subtitle, keywords, target) {
      target.kind = kind;
      target.boost = boost;
      target.title = searchField(title);
      target.subtitle = searchField(subtitle);
      target.keywords = { text: fold(keywords) };
      target.order = items.length;
      items.push(target);
    }

    each("main section[id]", function (section) {
      var heading = section.querySelector("h2");
      if (!heading) return;
      add("Section", 4, textOf(heading), textOf(section.querySelector(".section-intro")),
        textOf(section.querySelector(".kicker")), { element: section, hash: "#" + section.id });
    });
    each(".module-card", function (card) {
      add("Module", 4, textOf(card.querySelector("h3")), textOf(card.querySelector(".card-desc")), "",
        { element: card, hash: "#" + card.id });
    });
    each(".api-entry", function (entry) {
      var module = entry.id.split("-")[1];
      var name = textOf(entry.querySelector(".api-name"));
      var client = textOf(document.querySelector("#api-" + module + " .api-client code")).split("(")[0];
      var path = "aero." + module + (client ? "." + client : "");
      add(client ? "Method" : "Function", 3, name, path + " \u2014 " + textOf(entry.querySelector("dd")),
        "aero." + module + "." + name + " " + textOf(entry.querySelector("dt")),
        { element: entry, hash: "#" + entry.id });
    });
    each("form.calculator", function (form) {
      var labels = Array.prototype.map.call(form.querySelectorAll("label"), function (label) {
        return textOf(label);
      });
      add("Calculator", 3, textOf(form.querySelector("h3")),
        textOf(form.querySelector(".calc-module")) + " \u2014 " + labels.join(", "), "",
        { element: form, hash: "#" + form.id });
    });
    Object.keys(ENDPOINTS).forEach(function (module) {
      var explorer = explorers[module];
      if (!explorer) return;
      ENDPOINTS[module].forEach(function (endpoint, position) {
        var host = (/^https?:\/\/([^/]+)/.exec(endpoint.url) || [])[1] || "";
        var tags = (endpoint.tags || []).map(function (tag) {
          return TAG_LABELS[tag] || tag;
        });
        add("Endpoint", 2, endpoint.label, "Live explorer \u2014 aero." + module + " \u00b7 " + host,
          endpoint.url + " " + tags.join(" "),
          { element: explorer.form, hash: "#" + explorer.form.id, endpoint: { module: module, position: position } });
      });
    });
    each("li.update", function (update) {
      var meta = Array.prototype.map.call(update.querySelectorAll(".update-meta .tag, .update-meta time"), function (node) {
        return textOf(node);
      });
      add("Update", 2, textOf(update.querySelector("h3")), meta.join(" \u00b7 "),
        textOf(update.querySelector("h3 ~ p:not(.source-links)")), { element: update, hash: "#" + update.id });
    });
    each(".source-item", function (item) {
      var card = item.closest(".source-card");
      add("Source", 1, textOf(item.querySelector(".source-link code")), textOf(item.querySelector("p")),
        textOf(card && card.querySelector("h3")) + " " + textOf(item.querySelector(".source-tags")),
        { element: item, hash: card ? "#" + card.id : null });
    });
    each(".step", function (step) {
      add("Guide", 1, textOf(step.querySelector("h3"), ".step-number"), textOf(step.querySelector("pre code")),
        "install", { element: step, hash: "#install" });
    });
    return items;
  }

  function setupSearch() {
    var dialog = document.getElementById("search-dialog");
    var input = document.getElementById("search-input");
    var list = document.getElementById("search-results");
    var status = document.getElementById("search-status");
    if (!dialog || !input || !list || !status) return;
    if (typeof dialog.showModal !== "function") {
      each("[data-search-open], .shortcut-hint", function (element) {
        element.hidden = true;
      });
      return;
    }

    var MAX_RESULTS = 40;
    var index = null;
    var results = [];
    var active = -1;
    var opener = null;
    var navigating = false;
    var pressedOnBackdrop = false;

    function setActive(position, scroll) {
      var options = list.children;
      if (!options.length) {
        active = -1;
        input.removeAttribute("aria-activedescendant");
        return;
      }
      active = (position + options.length) % options.length;
      Array.prototype.forEach.call(options, function (option, i) {
        option.setAttribute("aria-selected", i === active ? "true" : "false");
      });
      var current = options[active];
      input.setAttribute("aria-activedescendant", current.id);
      if (scroll === false) return;
      var box = list.getBoundingClientRect();
      var rect = current.getBoundingClientRect();
      if (rect.top < box.top) list.scrollTop -= box.top - rect.top + 6;
      else if (rect.bottom > box.bottom) list.scrollTop += rect.bottom - box.bottom + 6;
    }

    function render() {
      list.textContent = "";
      results.forEach(function (result, position) {
        var option = document.createElement("li");
        option.id = "search-result-" + position;
        option.setAttribute("role", "option");
        option.setAttribute("aria-selected", "false");
        option.setAttribute("data-index", String(position));
        var kind = document.createElement("span");
        kind.className = "result-kind";
        kind.textContent = result.item.kind;
        var title = document.createElement("span");
        title.className = "result-title";
        appendHighlighted(title, result.item.title, result.marks.title);
        var subtitle = document.createElement("span");
        subtitle.className = "result-subtitle";
        appendHighlighted(subtitle, result.item.subtitle, result.marks.subtitle);
        option.appendChild(kind);
        option.appendChild(title);
        option.appendChild(subtitle);
        list.appendChild(option);
      });
    }

    function update() {
      if (!index) index = buildSearchIndex();
      var query = input.value.trim();
      var tokens = queryTokens(query);
      var found = [];
      if (!query) {
        index.forEach(function (item) {
          if (item.kind === "Section") found.push({ item: item, score: 0, marks: { title: [], subtitle: [] } });
        });
      } else if (tokens.length) {
        var phrase = tokens.join(" ");
        index.forEach(function (item) {
          var result = scoreItem(item, tokens, phrase);
          if (result) found.push(result);
        });
        found.sort(function (a, b) {
          return b.score - a.score || a.item.order - b.item.order;
        });
      }
      results = found.slice(0, MAX_RESULTS);
      render();
      list.scrollTop = 0;
      input.setAttribute("aria-expanded", results.length ? "true" : "false");
      setActive(0, false);

      var quoted = "\u201c" + query + "\u201d";
      if (!query) {
        status.textContent = "Jump to a section, or type to search " + index.length +
          " functions, endpoints, updates and sources.";
      } else if (!found.length) {
        status.textContent = "No results for " + quoted +
          ". Try a function name such as delta_v, or an agency such as ESA.";
      } else {
        status.textContent = (found.length === 1 ? "1 result" : found.length + " results") + " for " + quoted +
          (found.length > MAX_RESULTS ? ", showing the top " + MAX_RESULTS : "") + ".";
      }
    }

    function openPalette(query) {
      if (!dialog.open) {
        var focused = document.activeElement;
        opener = focused && focused !== document.body ? focused : null;
        document.documentElement.classList.add("is-search-open");
        dialog.showModal();
      }
      if (typeof query === "string") input.value = query;
      update();
      input.focus();
      input.select();
    }

    function closePalette() {
      if (dialog.open) dialog.close();
    }

    function choose(position) {
      var result = results[position];
      if (!result) return;
      var item = result.item;
      navigating = true;
      closePalette();
      if (item.endpoint) explorers[item.endpoint.module].choose(item.endpoint.position);
      goTo(item.element, { hash: item.hash, flash: shouldFlash(item.element) });
    }

    dialog.addEventListener("close", function () {
      document.documentElement.classList.remove("is-search-open");
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
      if (!navigating && opener && document.documentElement.contains(opener)) {
        try {
          opener.focus({ preventScroll: true });
        } catch (err) {
          opener.focus();
        }
      }
      navigating = false;
      opener = null;
    });

    // Close on a click that both starts and ends on the backdrop.
    dialog.addEventListener("pointerdown", function (event) {
      pressedOnBackdrop = event.target === dialog;
    });
    dialog.addEventListener("click", function (event) {
      if (event.target === dialog && pressedOnBackdrop) closePalette();
      pressedOnBackdrop = false;
    });

    input.addEventListener("input", update);
    input.addEventListener("keydown", function (event) {
      if (event.isComposing) return;
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        setActive(active + (event.key === "ArrowDown" ? 1 : -1));
      } else if (event.key === "Enter") {
        event.preventDefault();
        choose(active);
      } else if (event.key === "Escape") {
        event.preventDefault();
        closePalette();
      }
    });

    list.addEventListener("click", function (event) {
      var option = event.target.closest('[role="option"]');
      if (option) choose(Number(option.getAttribute("data-index")));
    });
    list.addEventListener("pointermove", function (event) {
      var option = event.target.closest('[role="option"]');
      if (!option) return;
      var position = Number(option.getAttribute("data-index"));
      if (position !== active) setActive(position, false);
    });

    each("[data-search-open]", function (button) {
      button.addEventListener("click", function () {
        openPalette();
      });
    });
    each("[data-search-close]", function (button) {
      button.addEventListener("click", closePalette);
    });

    document.addEventListener("keydown", function (event) {
      if (event.defaultPrevented || event.isComposing) return;
      var modifier = event.ctrlKey || event.metaKey;
      if ((event.key === "k" || event.key === "K") && modifier && !event.altKey && !event.shiftKey) {
        event.preventDefault();
        if (dialog.open) closePalette();
        else openPalette();
        return;
      }
      var target = event.target;
      var typing = target && (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName));
      if (event.key === "/" && !modifier && !event.altKey && !dialog.open && !typing) {
        event.preventDefault();
        openPalette();
      }
    });

    // Search engines and browsers use ?q= (see opensearch.xml and the JSON-LD SearchAction).
    var initialQuery = null;
    try {
      initialQuery = new URLSearchParams(window.location.search).get("q");
    } catch (err) {
      initialQuery = null;
    }
    if (initialQuery && initialQuery.trim()) openPalette(initialQuery.trim());
  }

  // ---------------------------------------------------------------------------
  // Scroll reveal. Nothing is hidden up front: elements animate only while they
  // rise into view from below, so jumping to a section never shows blank cards.

  function setupReveal() {
    if (reducedMotion || typeof IntersectionObserver !== "function") return;
    var targets = document.querySelectorAll(".section-head, .card, .calculator, .explorer, .api-module, .step");
    if (!targets.length) return;
    document.body.classList.add("animations-enabled");

    function enter(element, delay) {
      element.style.setProperty("--reveal-delay", delay + "ms");
      element.classList.add("is-entering");
    }

    var observer = new IntersectionObserver(
      function (entries) {
        var batch = 0;
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var element = entry.target;
          observer.unobserve(element);
          if (arrivingTarget && (element === arrivingTarget || element.contains(arrivingTarget))) return;
          if (entry.boundingClientRect.top < window.innerHeight * 0.85) return;
          enter(element, Math.min(batch * 60, 180));
          batch += 1;
        });
      },
      { rootMargin: "0px 0px 120px 0px" }
    );

    var viewport = window.innerHeight;
    var initial = 0;
    Array.prototype.forEach.call(targets, function (element) {
      var rect = element.getBoundingClientRect();
      if (rect.bottom < 0) return;
      if (rect.top < viewport + 120) {
        enter(element, Math.min(initial * 60, 180));
        initial += 1;
      } else {
        observer.observe(element);
      }
    });

    document.addEventListener("animationend", function (event) {
      var element = event.target;
      if (event.animationName === "rise-in" && element.classList && element.classList.contains("is-entering")) {
        element.classList.remove("is-entering");
        element.style.removeProperty("--reveal-delay");
      }
    });
  }

  function pauseOrbitArt() {
    var art = document.querySelector(".orbit-art");
    if (!reducedMotion || !art || typeof art.pauseAnimations !== "function") return;
    art.setCurrentTime(4);
    art.pauseAnimations();
  }

  // Each feature starts independently so one failure cannot disable the rest.
  [
    setupStarfield,
    setupSpotlight,
    setupScrollSpy,
    setupCountdowns,
    setupStats,
    setupTelemetry,
    setupCardCounts,
    setupShortcutLabels,
    setupApiToggle,
    setupAnchors,
    setupReveal,
    setupSearch,
    handleInitialHash,
    pauseOrbitArt
  ].forEach(function (setup) {
    try {
      setup();
    } catch (err) {
      if (window.console) window.console.error(err);
    }
  });
})();
