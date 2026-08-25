from dataclasses import dataclass

from mimosa.common import exp, log, soft_min


@dataclass(frozen=True)
class AdaptationCalibration:
    max_effectiveness_scale: float
    cost_param_scale: float


ADAPTATION_CALIBRATIONS = {
    "accreu": {
        "labourprod": AdaptationCalibration(1.0, 1.0),
        "riverine": AdaptationCalibration(1.0, 1.0),
        "slr": AdaptationCalibration(1.0, 1.0),
    },
    # Literature calibration targets discounted global BCRs of approximately
    # 2.4, 5, and 8 at 5% for labour, riverine flooding, and SLR respectively.
    # Regional rankings are retained by scaling the ACCREU maxima uniformly.
    "literature": {
        "labourprod": AdaptationCalibration(1.0, 1.0),
        "riverine": AdaptationCalibration(0.618, 1.0),
        "slr": AdaptationCalibration(0.659, 0.25),
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


def validate_adaptation_calibration(calibration, adaptation_type):
    """Validate a calibration name and its compatibility with model structure."""

    get_adaptation_calibration(calibration, "slr")
    if calibration == "literature" and adaptation_type == "combined":
        raise ValueError(
            "The literature ACCREU adaptation calibration requires "
            "'ACCREU adaptation: separate'."
        )


def adaptation_effectiveness_fct(
    adapt_costs, max_effectiveness, cost_param, effectiveness_scale_factor=1
):
    """
    Adaptation effectiveness function, based on the fitted function in ACCREU:
    Avoided damages = max_effectiveness * (1 - exp(-cost_param * adapt_costs))
    """

    return (
        effectiveness_scale_factor
        * max_effectiveness
        * (1 - exp(-cost_param * adapt_costs))
    )


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


def optimal_adaptation_costs_fct(gross_damages_abs, a, b, scale=0.01):
    if a * b == 0:
        return 0
    return soft_min(log(a * b * soft_min(gross_damages_abs, scale)) / b, scale)
