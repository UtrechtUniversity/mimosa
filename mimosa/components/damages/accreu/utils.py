from mimosa.common import exp


def adaptation_effectiveness_fct(adapt_costs, max_effectiveness, cost_param):
    """
    Adaptation effectiveness function, based on the fitted function in ACCREU:
    Avoided damages = max_effectiveness * (1 - exp(-cost_param * adapt_costs))
    """

    return max_effectiveness * (1 - exp(-cost_param * adapt_costs))
