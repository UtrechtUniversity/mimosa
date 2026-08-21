from mimosa.common import exp, log, soft_min


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
