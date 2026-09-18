// Browser port of the formulas implemented in the aero Python package.
(function () {
  "use strict";

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

  function format(value, digits) {
    return Number(value).toFixed(digits === undefined ? 3 : digits);
  }

  function readNumber(id) {
    var element = document.getElementById(id);
    var value = parseFloat(element.value);
    if (!isFinite(value)) {
      throw new RangeError(
        "Enter a number for “" + element.labels[0].textContent.trim() + "”"
      );
    }
    return value;
  }

  function render(outputId, compute) {
    var output = document.getElementById(outputId);
    try {
      output.textContent = compute();
      output.classList.remove("error");
    } catch (err) {
      output.textContent = err.message;
      output.classList.add("error");
    }
  }

  function updateAtmosphere() {
    render("atmosphere-output", function () {
      var h = readNumber("alt");
      return (
        "Temperature: " + format(temperature(h), 2) + " K\n" +
        "Pressure: " + format(pressure(h), 1) + " Pa\n" +
        "Density: " + format(density(h), 4) + " kg/m³\n" +
        "Speed of sound: " + format(speedOfSound(h), 2) + " m/s"
      );
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
      return (
        "Dynamic pressure: " + format(q, 1) + " Pa\n" +
        "Lift: " + format(q * area * cl, 1) + " N\n" +
        "Drag: " + format(q * area * cd, 1) + " N\n" +
        "L/D: " + format(cl / cd, 2) + "\n" +
        "Mach: " + format(v / speedOfSound(h), 3)
      );
    });
  }

  function updateOrbital() {
    render("orbital-output", function () {
      var altitude = readNumber("orb-alt");
      if (altitude < 0) throw new RangeError("altitude must be non-negative");
      var radius = EARTH_RADIUS + altitude * 1000;
      var period = orbitalPeriod(EARTH_MU, radius);
      return (
        "Orbital radius: " + format(radius / 1000, 1) + " km\n" +
        "Circular velocity: " + format(circularOrbitalVelocity(EARTH_MU, radius), 1) + " m/s\n" +
        "Period: " + format(period / 60, 2) + " min\n" +
        "Escape velocity: " + format(escapeVelocity(EARTH_MU, radius), 1) + " m/s"
      );
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
      return (
        "Exhaust velocity: " + format(ve, 1) + " m/s\n" +
        "Mass ratio: " + format(massRatio(m0, mf), 3) + "\n" +
        "Delta-v: " + format(deltaV(ve, m0, mf), 1) + " m/s\n" +
        "Propellant mass: " + format(propellant, 1) + " kg\n" +
        "Mass flow rate: " + format(flow, 2) + " kg/s\n" +
        "Burn time: " + format(burnTime(propellant, flow), 1) + " s\n" +
        "Thrust-to-weight: " + format(thrustToWeightRatio(thrustForce, m0), 2)
      );
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

  bind("atmosphere-form", updateAtmosphere);
  bind("aero-form", updateAerodynamics);
  bind("orbital-form", updateOrbital);
  bind("rocketry-form", updateRocketry);


  // Endpoint catalogue mirroring the Python data-service clients.
  var ENDPOINTS = {
    nasa: [
      {
        label: "apod() — Astronomy Picture of the Day",
        snippet: "nasa.NASAClient().apod()",
        url: "https://api.nasa.gov/planetary/apod",
        param: { label: "API key", value: "DEMO_KEY", query: "api_key" }
      },
      {
        label: "mars_rover_photos() — Curiosity photos",
        snippet: "nasa.NASAClient().mars_rover_photos(rover=\"curiosity\", sol=1000)",
        url: "https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos",
        query: { sol: "1000" },
        param: { label: "API key", value: "DEMO_KEY", query: "api_key" }
      },
      {
        label: "neo_feed() — near-Earth object feed",
        snippet: "nasa.NASAClient().neo_feed(start_date=\"2024-01-01\")",
        url: "https://api.nasa.gov/neo/rest/v1/feed",
        query: { start_date: "2024-01-01", end_date: "2024-01-02" },
        param: { label: "API key", value: "DEMO_KEY", query: "api_key" }
      },
      {
        label: "exoplanets() — Exoplanet Archive (no key)",
        snippet: "nasa.NASAClient().exoplanets(query=\"select top 5 pl_name from ps\")",
        url: "https://exoplanetarchive.ipac.caltech.edu/TAP/sync",
        query: { format: "json" },
        param: { label: "ADQL query", value: "select top 5 pl_name from ps", query: "query" }
      }
    ],
    esa: [
      {
        label: "open_data_search() — ESA Open Data Portal",
        snippet: "esa.ESAClient().open_data_search(query=\"satellite\", rows=5)",
        url: "https://data.esa.int/api/3/action/package_search",
        query: { rows: "5" },
        param: { label: "Search query", value: "satellite", query: "q" }
      },
      {
        label: "copernicus_products() — Sentinel products",
        snippet: "esa.ESAClient().copernicus_products(collection=\"SENTINEL-2\", top=5)",
        url: "https://catalogue.dataspace.copernicus.eu/odata/v1/Products",
        query: { $top: "5" },
        param: {
          label: "Collection",
          value: "SENTINEL-2",
          build: function (value) {
            return { $filter: "Collection/Name eq '" + value + "'" };
          }
        }
      },
      {
        label: "gaia_query() — Gaia Archive TAP",
        snippet: "esa.ESAClient().gaia_query(\"select top 5 * from gaiadr3.gaia_source\")",
        url: "https://gea.esac.esa.int/tap-server/tap/sync",
        query: { REQUEST: "doQuery", LANG: "ADQL", FORMAT: "json" },
        param: {
          label: "ADQL query",
          value: "select top 5 source_id from gaiadr3.gaia_source",
          query: "QUERY"
        }
      },
      {
        label: "neocc_risk_list() — NEOCC risk list",
        snippet: "esa.ESAClient().neocc_risk_list()",
        url: "https://neo.ssa.esa.int/tap/sync",
        query: { REQUEST: "doQuery", LANG: "ADQL", FORMAT: "json" },
        param: {
          label: "ADQL query",
          value: "select top 5 * from neocc.risk_list",
          query: "QUERY"
        }
      }
    ],
    iss: [
      {
        label: "current_location() — ISS ground track point",
        snippet: "iss.ISSClient().current_location()",
        url: "https://api.open-notify.org/iss-now.json"
      },
      {
        label: "people_in_space() — crew in orbit",
        snippet: "iss.ISSClient().people_in_space()",
        url: "https://api.open-notify.org/astros.json"
      },
      {
        label: "satellite_position() — ISS state vector",
        snippet: "iss.ISSClient().satellite_position()",
        url: "https://api.wheretheiss.at/v1/satellites/25544",
        param: { label: "Units", value: "kilometers", query: "units" }
      },
      {
        label: "tle() — latest ISS TLE",
        snippet: "iss.ISSClient().tle()",
        url: "https://api.wheretheiss.at/v1/satellites/25544/tles"
      },
      {
        label: "station_elements() — CelesTrak stations group",
        snippet: "iss.ISSClient().station_elements()",
        url: "https://celestrak.org/NORAD/elements/gp.php",
        query: { GROUP: "stations", FORMAT: "json" }
      }
    ],
    isro: [
      {
        label: "spacecrafts() — ISRO spacecraft",
        snippet: "isro.ISROClient().spacecrafts()",
        url: "https://isro.vercel.app/api/spacecrafts"
      },
      {
        label: "launchers() — ISRO launch vehicles",
        snippet: "isro.ISROClient().launchers()",
        url: "https://isro.vercel.app/api/launchers"
      },
      {
        label: "centres() — ISRO centres",
        snippet: "isro.ISROClient().centres()",
        url: "https://isro.vercel.app/api/centres"
      },
      {
        label: "launches() — Launch Library 2 launches",
        snippet: "isro.ISROClient().launches(limit=5)",
        url: "https://ll.thespacedevs.com/2.2.0/launch/previous/",
        query: { search: "ISRO", limit: "5", mode: "list" }
      },
      {
        label: "navic_elements() — NavIC (IRNSS) elements",
        snippet: "isro.ISROClient().navic_elements()",
        url: "https://celestrak.org/NORAD/elements/gp.php",
        query: { GROUP: "navic", FORMAT: "json" }
      }
    ]
  };

  function buildUrl(endpoint, paramValue) {
    var url = new URL(endpoint.url);
    var query = endpoint.query || {};
    Object.keys(query).forEach(function (key) {
      url.searchParams.set(key, query[key]);
    });
    if (endpoint.param && paramValue) {
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

  function preview(text, limit) {
    var max = limit === undefined ? 1200 : limit;
    return text.length > max ? text.slice(0, max) + "\n… truncated" : text;
  }

  function setupExplorer(form) {
    var endpoints = ENDPOINTS[form.dataset.module];
    if (!endpoints) return;

    var select = form.querySelector(".explorer-endpoint");
    var paramLabel = form.querySelector(".explorer-param-label");
    var paramInput = form.querySelector(".explorer-param");
    var snippet = form.querySelector(".explorer-snippet");
    var link = form.querySelector(".explorer-url");
    var output = form.querySelector(".explorer-output");

    endpoints.forEach(function (endpoint, index) {
      var option = document.createElement("option");
      option.value = String(index);
      option.textContent = endpoint.label;
      select.appendChild(option);
    });

    function current() {
      return endpoints[Number(select.value) || 0];
    }

    function refresh(resetParam) {
      var endpoint = current();
      if (endpoint.param) {
        paramLabel.hidden = false;
        paramLabel.firstChild.nodeValue = endpoint.param.label + " ";
        if (resetParam) paramInput.value = endpoint.param.value;
      } else {
        paramLabel.hidden = true;
        paramInput.value = "";
      }
      snippet.textContent = endpoint.snippet;
      var url = buildUrl(endpoint, paramInput.value);
      link.textContent = url;
      link.href = url;
    }

    function send() {
      var url = buildUrl(current(), paramInput.value);
      output.classList.remove("error");
      output.classList.add("loading");
      output.textContent = "Requesting …";
      fetch(url, { headers: { Accept: "application/json, text/plain, */*" } })
        .then(function (response) {
          return response.text().then(function (body) {
            output.classList.remove("loading");
            if (!response.ok) {
              output.classList.add("error");
              output.textContent =
                "Request failed with status " + response.status + "\n" + preview(body, 300);
              return;
            }
            var text = body;
            try {
              text = JSON.stringify(JSON.parse(body), null, 2);
            } catch (err) {
              /* not JSON: show the raw body */
            }
            output.textContent = preview(text);
          });
        })
        .catch(function (err) {
          output.classList.remove("loading");
          output.classList.add("error");
          output.textContent =
            "Browser request failed (" + err.message + "). The service may block " +
            "cross-origin calls — open the URL above, or run the Python snippet.";
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
  }

  Array.prototype.forEach.call(document.querySelectorAll(".explorer"), setupExplorer);

  // Entrance animations, disabled when the visitor prefers reduced motion.
  function setupAnimations() {
    var reduced =
      window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var targets = document.querySelectorAll(
      ".card, .calculator, .explorer, .section h2, .section-intro, .code"
    );
    if (reduced || typeof IntersectionObserver !== "function") {
      Array.prototype.forEach.call(targets, function (element) {
        element.classList.add("is-visible");
      });
      return;
    }
    document.body.classList.add("animations-enabled");
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -10% 0px", threshold: 0.05 }
    );
    Array.prototype.forEach.call(targets, function (element, index) {
      element.classList.add("reveal");
      element.style.setProperty("--reveal-delay", (index % 6) * 60 + "ms");
      observer.observe(element);
    });

    // Safety net: never leave content hidden if the observer does not fire.
    window.setTimeout(function () {
      Array.prototype.forEach.call(targets, function (element) {
        element.classList.add("is-visible");
      });
    }, 3000);
  }

  setupAnimations();
})();
