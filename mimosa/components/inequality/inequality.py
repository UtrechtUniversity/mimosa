import scipy.stats as stats
import numpy as np
from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    Constraint,
    Equation,
    RegionalEquation,
    GlobalEquation,
    value,
    soft_max,
    Any,
    exp,
    quant,
)

# class RegionalQuintileConstraint(GeneralConstraint):
#     def to_pyomo_constraint(self, m):
#         return Constraint(m.t, m.regions, m.quintiles, rule=self.rule, doc=self.doc)


def get_constraints(m: AbstractModel):
    """
    This component uses a GINI-coefficient and an average income for each region to calculate the median income per quintile
    """

    constraints = []

    # 1. Calculate standard deviation (sigma) from GINI for each region
    # σ = √2 × Φ⁻¹((GINI + 1)/2)
    def calculate_sigma(m, r):
        gini = m.GINI[r]
        gini_converted = (gini + 1) / 2
        z_score = stats.norm.ppf(gini_converted)  # Φ⁻¹((GINI + 1)/2)
        sigma = np.sqrt(2) * z_score
        return sigma

    m.inequality_sigma = Param(m.regions, initialize=calculate_sigma)
    m.inequality_z_score = Param(
        m.quintiles,
        initialize=lambda m, q: stats.norm.ppf((q - 0.5) / len(m.quintiles)),
    )

    # 2. Equation for expected, median incomes per quintile
    # income of percentile = mean_income × e^(σ × Φ⁻¹(p) - 0.5 × σ²)
    def quintile_income_eq(m, t, r, q):
        # Retrieve underlying data
        gdp_per_capita = m.GDP_net[t, r] / m.population[t, r]
        # Standard deviation for this region
        sigma = m.inequality_sigma[r]
        # Z-score for midpoint
        z_score = m.inequality_z_score[q]
        # Calculate log-income with correction term
        log_income = sigma * z_score - 0.5 * sigma**2
        # Calculate expected income for this quintile
        expected_income = gdp_per_capita * np.exp(log_income)

        return expected_income

    constraints.extend(
        [
            Equation(
                m.income_quintile,
                quintile_income_eq,
                [m.t, m.regions, m.quintiles],
            )
        ]
    )

    # Return the list of constraints
    return constraints
