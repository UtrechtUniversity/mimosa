"""Tables for the coefficients used by the sea-level-rise component."""

from textwrap import indent

from pyomo.environ import value

from mimosa.components.sealevelrise import SLR_PROJECTION_PARAMETER_SETS


# Presentation metadata only: numerical values come from the component's
# projection sets and the documentation model's initialized parameters.
SLR_COEFFICIENT_GROUPS = {
    "initial": (
        ("slr_reference_year", r"y_{\mathrm{ref}}", "Sea-level reference year", "year"),
        ("slr_initial_year", r"y_{\mathrm{init}}", "Historical calibration year", "year"),
        ("slr_thermal_fast_init", r"S_{\mathrm{fast,init}}", "Initial fast thermal-expansion contribution", "m"),
        ("slr_thermal_slow_init", r"S_{\mathrm{slow,init}}", "Initial slow thermal-expansion contribution", "m"),
        ("slr_gsic_init", r"S_{\mathrm{GL,init}}", "Initial glacier contribution", "m"),
        ("slr_gis_init", r"S_{\mathrm{GIS,init}}", "Initial Greenland contribution", "m"),
        ("slr_ais_init", r"S_{\mathrm{AIS,init}}", "Initial Antarctic contribution", "m"),
        ("slr_ais_ocean_temp_init", r"T_{\mathrm{A,init}}", "Initial Antarctic ocean-temperature proxy", "°C above pre-industrial"),
    ),
    "thermal": (
        ("slr_thermal_fast_sensitivity", r"\beta_{\mathrm{fast}}", "Fast equilibrium sensitivity", "m/°C"),
        ("slr_thermal_slow_sensitivity", r"\beta_{\mathrm{slow}}", "Slow equilibrium sensitivity", "m/°C"),
        ("slr_thermal_fast_timescale", r"\tau_{\mathrm{fast}}", "Fast response time", "years"),
        ("slr_thermal_slow_timescale", r"\tau_{\mathrm{slow}}", "Slow response time", "years"),
    ),
    "glaciers": (
        ("slr_gsic_total_ice", r"P_{\mathrm{GL}}", "Glacier sea-level potential", "m"),
        ("slr_gsic_temp_sensitivity", r"\zeta_{\mathrm{GL}}", "Equilibrium temperature scale", "°C"),
        ("slr_gsic_timescale", r"\tau_{\mathrm{GL}}", "Glacier response time", "years"),
    ),
    "greenland": (
        ("slr_gis_total_ice", r"P_{\mathrm{GIS}}", "Greenland sea-level potential", "m"),
        ("slr_gis_threshold", r"T_c", "Equilibrium transition temperature", "°C above pre-industrial"),
        ("slr_gis_transition_width", r"w", "Equilibrium transition width", "°C"),
        ("slr_gis_base_timescale", r"\tau_0", "Response time at zero warming", "years"),
        ("slr_gis_timescale_sensitivity", r"\gamma", "Response-time sensitivity to warming", "1/°C"),
    ),
    "antarctica": (
        ("slr_ais_total_ice", r"P_{\mathrm{AIS}}", "Effective vulnerable Antarctic ice stock", "m"),
        ("slr_ais_ocean_temp_scaling", r"\lambda_A", "Ocean-temperature scaling", "dimensionless"),
        ("slr_ais_ocean_temp_timescale", r"\tau_A", "Ocean-temperature response time", "years"),
        ("slr_ais_background_rate", r"r_0", "Background ice-loss rate", "m/year"),
        ("slr_ais_temp_sensitivity", r"r_1", "Ice-loss sensitivity to ocean temperature", "m/(year · °C)"),
        ("slr_ais_fast_rate", r"r_f", "Additional fast-response rate", "m/year"),
        ("slr_ais_fast_threshold", r"T_{crit}", "Fast-response threshold temperature", "°C above pre-industrial"),
        ("slr_ais_fast_transition_width", r"w_A", "Fast-response transition width", "°C"),
    ),
    "land_water": (
        ("slr_lws_rate", r"r_{\mathrm{LWS}}", "Future land-water-storage contribution rate", "m/year"),
    ),
}


def _table(rows, headers):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return '<div class="tiny_table" markdown="1">\n\n' + "\n".join(lines) + "\n\n</div>"


def render_slr_coefficients(section, model):
    """Render one collapsed block without constructing any additional models."""
    fixed, varying = [], []
    for name, symbol, description, unit in SLR_COEFFICIENT_GROUPS[section]:
        cells = [f"${symbol}$", description, unit]
        key = name[len("slr_"):]
        if key in SLR_PROJECTION_PARAMETER_SETS["central"]:
            varying.append(cells + [
                format(SLR_PROJECTION_PARAMETER_SETS[projection][key], ".6g")
                for projection in ("low", "central", "high")
            ])
        else:
            fixed.append(cells + [format(value(getattr(model, name)), ".6g")])

    parts = []
    if section == "initial":
        title = "Reference years and initial values"
        parts.append(
            "These values are shared by all three projections. Initial sea-level "
            "contributions are relative to the reference year and specified at the "
            "historical calibration year. At other start years, the model scales "
            "the initial values as described above. The land-water-storage anomaly "
            "starts at zero."
        )
    else:
        title = "Coefficients"
    if varying:
        parts.append(_table(varying, ["Symbol", "Meaning", "Units", "Low", "Central (default)", "High"]))
    if fixed:
        if varying:
            parts.append("The following constants are shared by all three projections.")
        parts.append(_table(fixed, ["Symbol", "Meaning", "Units", "Value"]))
    return f'??? parameter "{title}"\n\n' + indent("\n\n".join(parts), "    ") + "\n"
