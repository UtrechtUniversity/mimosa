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

# e = 0.64

# class RegionalQuintileConstraint(GeneralConstraint):
#     def to_pyomo_constraint(self, m):
#         return Constraint(m.t, m.regions, m.quintiles, rule=self.rule, doc=self.doc)


def get_constraints(m: AbstractModel):
    """
    This component calculates the following:
    1. It uses a GINI-coefficient and an average income for each region to calculate the median income per quintile
    2. It calculates the damage per quintile using elasticities
    3. It calculates the actual damage per quintile by scaling the distribution with total damages
    4. Income after damages per quintile
    """

    constraints = []

    # ============================================================================
    # PARAMETERS
    # ============================================================================

    # GINI-coefficient per region (from CSV)
    m.GINI = Param(m.regions, doc="regional::inequality.GINI")
    # m.GINI = Param(m.regions, initialize=lambda m, r: 0.45)  # DEBUG: Test zonder CSV

    # Elasticity parameter for damage distribution (ε)
    m.damage_elasticity = Param(doc="::inequality.damage_elasticity")

    # ============================================================================
    # VARIABLES
    # ============================================================================

    # m.average_income = Param(m.t, m.regions, units=quant.unit("currency_unit"))

    # Income for each median person in a quintile
    m.income_quintile_median = Var(
        m.t,
        m.regions,
        m.quintiles,
        units=quant.unit("currency_unit / (billion people)"),
    )

    # Average income per quintile
    m.income_quintile_average = Var(
        m.t, m.regions, m.quintiles, units=quant.unit("currency_unit")
    )

    # Distribution of damages per quintile (without scaling) fer median point: income_quintile^ε
    m.damage_distribution_median = Var(
        m.t, m.regions, m.quintiles, units=quant.unit("currency_unit")
    )

    # Distribution of damages per quintile (without scaling) for average of quintile: income_quintile^ε
    m.damage_distribution_average = Var(
        m.t, m.regions, m.quintiles, units=quant.unit("currency_unit")
    )

    # Sum of damage_distributio_median over all quintiles (intermediate step for scaling factor)
    m.sum_damage_distribution_median = Var(
        m.t, m.regions, units=quant.unit("currency_unit")
    )

    # Sum of damage_distribution_average over all quintiles (intermediate step for scaling factor)
    m.sum_damage_distribution_average = Var(
        m.t, m.regions, units=quant.unit("currency_unit")
    )

    # Scaling factor C for each region and timestep: total_damage / sum(damage_distribution)
    # median and average values can both be used. Average is most correct.
    m.damage_scaling_factor = Var(m.t, m.regions, units=quant.unit("currency_unit"))

    # Actual damage per quintile: C * income_quintile^ε
    m.damage_quintile = Var(
        m.t, m.regions, m.quintiles, units=quant.unit("currency_unit")
    )

    # Income after damages per quintile
    m.income_after_damages = Var(
        m.t, m.regions, m.quintiles, units=quant.unit("currency_unit")
    )

    # Relative income loss per quintile (percentage)
    m.relative_income_loss = Var(
        m.t, m.regions, m.quintiles, units=quant.unit("percent")
    )

    # ============================================================================
    # INCOME PER QUINTILE
    # ============================================================================

    # 1. Calculate standard deviation (sigma) from GINI for each region
    # σ = √2 × Φ⁻¹((GINI + 1)/2)
    def calculate_sigma(m, r):
        gini = m.GINI[r]
        gini_converted = (gini + 1) / 2
        z_score = stats.norm.ppf(gini_converted)  # Φ⁻¹((GINI + 1)/2)
        sigma = np.sqrt(2) * z_score
        return sigma

    m.inequality_sigma = Param(m.regions, initialize=calculate_sigma)

    # Z-SCORES FOR QUINTILE BOUNDARIES AND MIDPOINTS

    # Midpoints for each quintile (0.1, 0.3, 0.5, 0.7, 0.9)
    m.inequality_z_score_midpoint = Param(
        m.quintiles,
        initialize=lambda m, q: stats.norm.ppf((q - 0.5) / len(m.quintiles)),
    )

    # Lower bounds for each quintile (0.0, 0.2, 0.4, 0.6, 0.8)
    m.inequality_z_score_lower = Param(
        m.quintiles,
        initialize=lambda m, q: (
            stats.norm.ppf((q - 1) / len(m.quintiles)) if q > 1 else -np.inf
        ),
    )

    # Upper bounds for each quintile (0.2, 0.4, 0.6, 0.8, 1.0)
    m.inequality_z_score_upper = Param(
        m.quintiles,
        initialize=lambda m, q: stats.norm.ppf(q / len(m.quintiles)),
    )

    # 2. Equation for expected, median incomes per quintile
    # income of percentile = mean_income × e^(σ × Φ⁻¹(p) - 0.5 × σ²)
    def quintile_income_eq(m, t, r, q):
        # Retrieve underlying data
        gdp_per_capita = (
            m.GDP_net[t, r] + m.damage_costs[t, r] * m.GDP_gross[t, r]
        ) / m.population[t, r]
        # Standard deviation for this region
        sigma = m.inequality_sigma[r]
        # Z-score for midpoint
        z_score = m.inequality_z_score_midpoint[q]
        # Calculate log-income with correction term
        log_income = sigma * z_score - 0.5 * sigma**2
        # Calculate expected income for this quintile
        expected_income = gdp_per_capita * np.exp(log_income)

        return expected_income

    constraints.extend(
        [
            Equation(
                m.income_quintile_median,
                quintile_income_eq,
                [m.t, m.regions, m.quintiles],
            )
        ]
    )

    # ============================================================================
    # AVERAGE INCOME PER QUINTILE
    # ============================================================================

    def quintile_average_income_eq(m, t, r, q):
        gdp_per_capita = (
            m.GDP_net[t, r] + m.damage_costs[t, r] * m.GDP_gross[t, r]
        ) / m.population[t, r]
        sigma = m.inequality_sigma[r]

        z_lower = m.inequality_z_score_lower[q]
        z_upper = m.inequality_z_score_upper[q]

        if q == 1:
            # Q1: from -∞ to 20th percentile
            p_upper = 0.2
            truncation_factor = stats.norm.cdf(sigma - z_upper) / p_upper
        elif q == 5:
            # Q5: from 80th percentile to ∞
            p_lower = 0.8
            # For the top quintile, we need a different formula
            # E[Y | Y > y_p] = mean × [1 - Φ(σ - z_lower)] / (1 - p_lower)
            truncation_factor = (1 - stats.norm.cdf(sigma - z_lower)) / (1 - p_lower)
        else:
            # Q2, Q3, Q4: interior quintiles
            p_lower = (q - 1) * 0.2
            p_upper = q * 0.2
            numerator = stats.norm.cdf(sigma - z_lower) - stats.norm.cdf(
                sigma - z_upper
            )
            denominator = p_upper - p_lower
            truncation_factor = numerator / denominator

        avg_income = gdp_per_capita * truncation_factor
        return avg_income

    constraints.extend(
        [
            Equation(
                m.income_quintile_average,
                quintile_average_income_eq,
                [m.t, m.regions, m.quintiles],
            )
        ]
    )

    # ============================================================================
    # DAMAGE DISTRIBUTION PER QUINTILE (median)
    # ============================================================================

    def damage_distribution_me_eq(m, t, r, q):
        # calculate income_quintile^ε
        income = m.income_quintile_median[t, r, q]
        epsilon = m.damage_elasticity
        return income**epsilon

    constraints.extend(
        [
            Equation(
                m.damage_distribution_median,
                damage_distribution_me_eq,
                [m.t, m.regions, m.quintiles],
            )
        ]
    )

    # ============================================================================
    # DAMAGE DISTRIBUTION PER QUINTILE (average - as intermediate step for calculating scaling factor later)
    # ============================================================================

    def damage_distribution_av_eq(m, t, r, q):
        # calculate income_quintile^ε
        income = m.income_quintile_average[t, r, q]
        epsilon = m.damage_elasticity
        return income**epsilon

    constraints.extend(
        [
            Equation(
                m.damage_distribution_average,
                damage_distribution_av_eq,
                [m.t, m.regions, m.quintiles],
            )
        ]
    )

    # ============================================================================
    # SUM OF DAMAGE DISTRIBUTION (median) (for scaling factor)
    # ============================================================================

    def sum_damage_distribution_eq(m, t, r):
        return sum(m.damage_distribution_median[t, r, q] for q in m.quintiles)

    constraints.extend(
        [
            Equation(
                m.sum_damage_distribution_median,
                sum_damage_distribution_eq,
                [m.t, m.regions],
            )
        ]
    )

    # ============================================================================
    # SUM OF DAMAGE DISTRIBUTION (average) (for scaling factor)
    # ============================================================================

    def sum_damage_distribution_eq(m, t, r):
        return sum(m.damage_distribution_average[t, r, q] for q in m.quintiles)

    constraints.extend(
        [
            Equation(
                m.sum_damage_distribution_average,
                sum_damage_distribution_eq,
                [m.t, m.regions],
            )
        ]
    )

    # ============================================================================
    # SCALING FACTOR C: total_damage / sum(damage_distribution)
    # ============================================================================

    def damage_scaling_factor_eq(m, t, r):
        # C = total_damage / sum(damage_distribution)
        return m.damage_costs_abs[t, r] / (
            (m.sum_damage_distribution_average[t, r])
            * (m.population[t, r] / len(m.quintiles))
        )

    constraints.extend(
        [
            Equation(
                m.damage_scaling_factor,
                damage_scaling_factor_eq,
                [m.t, m.regions],
            )
        ]
    )
    # ============================================================================
    # ACTUAL DAMAGE PER QUINTILE: damage_quintile = C * damage_distribution
    # ============================================================================

    def damage_quintile_eq(m, t, r, q):
        return m.damage_scaling_factor[t, r] * m.damage_distribution_median[t, r, q]

    constraints.extend(
        [
            Equation(
                m.damage_quintile,
                damage_quintile_eq,
                [m.t, m.regions, m.quintiles],
            )
        ]
    )

    # ============================================================================
    # INCOME AFTER DAMAGES PER QUINTILE
    # ============================================================================

    def income_after_damages_eq(m, t, r, q):
        return m.income_quintile_median[t, r, q] - m.damage_quintile[t, r, q]

    constraints.extend(
        [
            Equation(
                m.income_after_damages,
                income_after_damages_eq,
                [m.t, m.regions, m.quintiles],
            )
        ]
    )

    # ============================================================================
    # Relative income loss per quintile (percentage)
    # ============================================================================

    def relative_income_loss_eq(m, t, r, q):
        income_before = m.income_quintile_median[t, r, q]
        income_after = m.income_after_damages[t, r, q]
        # Avoid division by zero
        return (income_before - income_after) / (income_before + 1e-10) * 100

    constraints.extend(
        [
            Equation(
                m.relative_income_loss,
                relative_income_loss_eq,
                [m.t, m.regions, m.quintiles],
            )
        ]
    )

    # Return the list of constraints
    return constraints
