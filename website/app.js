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
})();
