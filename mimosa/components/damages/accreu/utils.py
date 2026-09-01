from dataclasses import dataclass
from typing import Mapping

from mimosa.common import exp, log, soft_min, RegionalConstraint, Constraint, value


@dataclass(frozen=True)
class AdaptationCalibration:
    max_effectiveness_scale: float
    cost_multiplier: float


@dataclass(frozen=True)
class AdaptationOptions:
    adaptation_type: str
    determination: str
    calibrations: Mapping[str, AdaptationCalibration]

    @property
    def uses_analytical_adaptation(self):
        """Whether adaptation is calculated analytically rather than optimised."""

        return self.determination == "analytical_optimum"


ADAPTATION_CALIBRATIONS = {
    "accreu": {
        "labourprod": AdaptationCalibration(1.0, 1.0),
        "riverine": AdaptationCalibration(1.0, 1.0),
        "slr": AdaptationCalibration(1.0, 1.0),
        "combined": AdaptationCalibration(1.0, 1.0),
    },
    # Conservative end of the literature envelope: lower realised
    # effectiveness and higher implementation costs.
    "literature_low": {
        "labourprod": AdaptationCalibration(0.741, 6.0),
        "riverine": AdaptationCalibration(0.412, 6.0),
        "slr": AdaptationCalibration(0.439, 8.0),
        "combined": AdaptationCalibration(0.645, 6.0),
    },
    # Literature calibration targets discounted global BCRs of approximately
    # 2.4, 5, 8, and 4.3 at 5% for labour, riverine flooding, SLR, and combined
    # labour-river adaptation respectively.
    # Regional rankings are retained by scaling the ACCREU maxima uniformly.
    "literature": {
        "labourprod": AdaptationCalibration(1.0, 1.0),
        "riverine": AdaptationCalibration(0.618, 1.0),
        "slr": AdaptationCalibration(0.659, 4.0),
        "combined": AdaptationCalibration(0.889, 1.0),
    },
    # Optimistic end of the literature envelope: higher realised
    # effectiveness and lower implementation costs.
    "literature_high": {
        "labourprod": AdaptationCalibration(1.977, 0.5),
        "riverine": AdaptationCalibration(0.721, 0.5),
        "slr": AdaptationCalibration(0.933, 2.0),
        "combined": AdaptationCalibration(1.25, 0.25),
    },
}


def get_adaptation_calibration(calibration, sector):
    """Return the sectoral factors for an ACCREU adaptation calibration."""

    try:
        return ADAPTATION_CALIBRATIONS[calibration][sector]
    except KeyError as exc:
        if calibration not in ADAPTATION_CALIBRATIONS:
            raise ValueError(
                f"Unknown ACCREU adaptation calibration: {calibration}"
            ) from exc
        raise ValueError(f"Unknown ACCREU adaptation sector: {sector}") from exc


def validate_adaptation_calibration(calibration):
    """Validate an adaptation calibration name."""

    get_adaptation_calibration(calibration, "slr")


def get_adaptation_options(context):
    """Read and validate all ACCREU adaptation options once."""

    adaptation_type = context.option("damage", "ACCREU_adaptation")
    calibration_name = context.option(
        "damage", "ACCREU_adaptation_calibration", default="accreu"
    )
    validate_adaptation_calibration(calibration_name)

    sectors = ["labourprod", "riverine", "slr"]
    if adaptation_type == "combined":
        sectors.append("combined")

    return AdaptationOptions(
        adaptation_type=adaptation_type,
        determination=context.option("damage", "ACCREU_adaptation_determination"),
        calibrations={
            sector: get_adaptation_calibration(calibration_name, sector)
            for sector in sectors
        },
    )


def effective_adaptation_curve(
    m, r, source_max_effectiveness, source_cost_param, calibration
):
    """Return adaptation curve coefficients in MIMOSA's model units."""

    effective_max = (
        source_max_effectiveness
        * calibration.max_effectiveness_scale
        * m.adaptation_effectiveness_scale_factor
    )
    effective_cost_param = (
        source_cost_param
        / calibration.cost_multiplier
        / m.dollar_2017_MER_to_2010_PPP[r]
    )
    return effective_max, effective_cost_param


def adaptation_effectiveness_fct(adapt_costs, max_effectiveness, cost_param):
    """
    Adaptation effectiveness function, based on the fitted function in ACCREU:
    Avoided damages = max_effectiveness * (1 - exp(-cost_param * adapt_costs))
    """

    return max_effectiveness * (1 - exp(-cost_param * adapt_costs))


def dmg_fct_linear(m, t, a, b, xshift=0, remove_base=True):
    def fct(x):
        return a + b * x

    x_t = m.temperature[t]
    x_0 = m.temperature[0]
    if remove_base:
        return fct(x_t - xshift) - fct(x_0 - xshift)
    return fct(x_t - xshift)


def dmg_fct_power(m, t, a, b, c, x="temperature", xshift=0, remove_base=True):
    if x not in ["temperature", "total_SLR"]:
        raise ValueError("x must be either 'temperature' or 'total_SLR'")

    def fct(x):
        return a + b * x**c

    x_t = getattr(m, x)[t]
    x_0 = getattr(m, x)[0]
    if remove_base:
        return fct(x_t - xshift) - fct(x_0 - xshift)
    return fct(x_t - xshift)


def optimal_adaptation_costs_fct(m, t, gross_damages_abs, a, b, scale=0.001):
    if a * b == 0:
        return 0
    if m.delay_adaptation_year is not False and m.year(t) <= m.delay_adaptation_year:
        return 0
    return soft_min(log(a * b * soft_min(gross_damages_abs, scale)) / b, scale)


def get_delayed_adaptation_constraint(varname, threshold=0.00005):

    constraint = RegionalConstraint(
        lambda m, t, r: (
            getattr(m, varname)[t, r] <= threshold
            if value(m.delay_adaptation_year) is not False
            and m.year(t) <= m.delay_adaptation_year
            else Constraint.Skip
        )
    )
    return constraint
