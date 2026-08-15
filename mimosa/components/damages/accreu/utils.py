from mimosa.common import GlobalEquation, Var, exp, log, quant, soft_min


def add_global_costs_from_relative(m, constraints, regional_costs):
    """Add global costs from regional costs expressed as fractions of GDP."""
    regional_name = regional_costs.name
    global_name = f"global_{regional_name}"

    setattr(
        m,
        global_name,
        Var(m.t, units=quant.unit("fraction_of_GDP")),
    )
    constraints.append(
        GlobalEquation(
            getattr(m, global_name),
            lambda m, t: (
                sum(
                    getattr(m, regional_name)[t, r] * m.GDP_gross[t, r]
                    for r in m.regions
                )
                / m.global_GDP_gross[t]
            ),
        )
    )


def add_global_costs_from_absolute(m, constraints, regional_costs_abs):
    """Add global costs from regional costs expressed in currency units."""
    regional_name = regional_costs_abs.name
    if not regional_name.endswith("_abs"):
        raise ValueError("Absolute regional cost variable name must end in '_abs'")

    global_name = f"global_{regional_name[:-4]}"

    setattr(
        m,
        global_name,
        Var(m.t, units=quant.unit("fraction_of_GDP")),
    )
    constraints.append(
        GlobalEquation(
            getattr(m, global_name),
            lambda m, t: (
                sum(getattr(m, regional_name)[t, r] for r in m.regions)
                / m.global_GDP_gross[t]
            ),
        )
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


def dmg_fct_linear(m, t, a, b):

    def fct(x):
        return a + b * x

    return fct(m.temperature[t]) - fct(m.temperature[0])


def dmg_fct_power(m, t, a, b, c, x="temperature"):

    if x not in ["temperature", "total_SLR"]:
        raise ValueError("x must be either 'temperature' or 'total_SLR'")

    def fct(x):
        return a + b * x**c

    x_t = getattr(m, x)[t]
    x_0 = getattr(m, x)[0]
    return fct(x_t) - fct(x_0)


def optimal_adaptation_costs_fct(gross_damages_abs, a, b, scale=0.01):
    if a * b == 0:
        return 0
    return soft_min(log(a * b * soft_min(gross_damages_abs, scale)) / b, scale)
