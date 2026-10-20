"""
Utils to calculate TFP using the Cobb-Douglas equation
"""

from mimosa.common import value


def get_TFP_value(m, t, r):

    alpha = value(m.alpha)
    dk = value(m.dk)
    sr = value(m.sr)

    # Calculate the capital stock at time t
    for s in range(t + 1):
        if s == 0:
            # Initial capital stock
            capital = value(m.init_capitalstock_factor[r] * m.baseline_GDP[0, r])
        else:
            # For the subsequent years, calculate the capital stock with the stock growth formula
            period_length = value(m.period_length[s])
            investments = sr * baseline_gdp
            dKdt = calc_dKdt(capital, dk, investments, period_length)
            capital = dKdt * period_length + capital
        baseline_gdp = value(m.baseline_GDP[s, r])

    # Calculate the TFP using the Cobb-Douglas equation
    population = value(m.population[s, r])
    tfp = baseline_gdp / calc_GDP(1, population, capital, alpha)

    return tfp


def calc_dKdt(K, dk, I, dt):
    """
    $$ \\frac{\\partial \\href{./#var__capital_stock}{K_{t,r}}}{\\partial t} = \\frac{1}{\\Delta t} \\cdot ((1 - \\href{./#param__economics.GDP.depreciation of capital}{\\text{dk}})^{\\Delta t}  - 1) \\cdot \\href{./#var__capital_stock}{K_{t,r}} + \\href{./#var__investments}{I_{t,r}}.$$
    """
    return ((1 - dk) ** dt - 1) / dt * K + I


def calc_GDP(TFP, L, K, alpha):
    """
    $$ \\href{./#var__GDP_gross}{\\text{GDP}_{\\text{gross},t,r}} = \\text{TFP}\\_{t,r} \\cdot L^{1-\\href{./#param__economics.GDP.alpha}{\\alpha}}\\_{t,r} \\cdot \\left(\\href{./#var__capital_stock}{K\\_{t,r}}\\right)^{\\href{./#param__economics.GDP.alpha}{\\alpha}}, $$
    with $\\text{TFP}$ the total factor productivity (exogenously calibrated from the baseline SSP scenarios)
    $L$ the labor (represented by the total population), $\\href{./#var__capital_stock}{K}$ the capital stock and $\\href{./#param__economics.GDP.alpha}{\\alpha}$ the share of capital in the production function.

    """
    return TFP * L ** (1 - alpha) * K**alpha
