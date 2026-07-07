from mimosa.common import exp, log, soft_min


def adaptation_effectiveness_fct(adapt_costs, max_effectiveness, cost_param):
    """
    Adaptation effectiveness function, based on the fitted function in ACCREU:
    Avoided damages = max_effectiveness * (1 - exp(-cost_param * adapt_costs))
    """

    return max_effectiveness * (1 - exp(-cost_param * adapt_costs))


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
