"""
Utils to calculate TFP using the Cobb-Douglas equation
"""

from mimosa.common import value


def get_TFP_value(m, t, r):

    alpha = value(m.alpha)
    dt = value(m.dt)
    dk = value(m.dk)
    sr = value(m.sr)

    # Calculate the capital stock at time t
    for s in range(t + 1):
        if s == 0:
            # Initial capital stock
            capital = value(m.init_capitalstock_factor[r] * m.baseline_GDP[0, r])
        else:
            # For the subsequent years, calculate the capital stock with the stock growth formula
            investments = sr * baseline_gdp
            dKdt = calc_dKdt(capital, dk, investments, dt)
            capital = dKdt * dt + capital
        baseline_gdp = value(m.baseline_GDP[s, r])

    # Calculate the TFP using the Cobb-Douglas equation
    population = value(m.population[s, r])
    tfp = baseline_gdp / calc_GDP(1, population, capital, alpha)

    return tfp


def calc_dKdt(K, dk, I, dt):
    """
    $$ \\frac{\\partial K_{t,r}}{\\partial t} = \\frac{1}{\\Delta t} \\cdot ((1 - dk)^{\\Delta t}  - 1) \\cdot K_{t,r} + I_{t,r}.$$
    """
    return ((1 - dk) ** dt - 1) / dt * K + I


def calc_GDP(TFP, L, K, alpha):
    """
    $$ \\text{GDP}_{\\text{gross},t,r} = \\text{TFP}\\_{t,r} \\cdot L^{1-\\alpha}\\_{t,r} \\cdot K^{\\alpha}\\_{t,r}, $$
    with $\\text{TFP}$ the total factor productivity (exogenously calibrated from the baseline SSP scenarios)
    $L$ the labor (represented by the total population), $K$ the capital stock and $\\alpha$ the share of capital in the production function.

    """
    return TFP * L ** (1 - alpha) * K**alpha
