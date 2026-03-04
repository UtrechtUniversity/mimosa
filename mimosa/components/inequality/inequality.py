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

#e = 0.64

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

    # Income per quintile
    m.income_quintile = Var(
        m.t, m.regions, m.quintiles, units=quant.unit("currency_unit")
    )

    # Distribution of damages per quintile (without scaling): income_quintile^ε
    m.damage_distribution = Var(
        m.t, m.regions, m.quintiles, units=quant.unit("currency_unit")
    )

    # Sum of damage_distribution over all quintiles (for scaling factor)
    m.sum_damage_distribution = Var(
        m.t, m.regions, units=quant.unit("currency_unit")
    )

    # Scaling factor C for each region and timestep: toal_damage / sum(damage_distribution)
    m.damage_scaling_factor = Var(
        m.t, m.regions, units=quant.unit("currency_unit")
    )

    # Actual damage per quintile: C * income_quintile^ε
    m.damage_quintile = Var(
        m.t, m.regions, m.quintiles, units=quant.unit("currency_unit")
    )

    # Income after damages per quintile 
    m.income_after_damages = Var(
        m.t, m.regions, m.quintiles, units=quant.unit("currency_unit")
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

    # Calculate z-scores for quintile midpoints
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
    
    constraints.extend([
        Equation(
            m.income_quintile,
            quintile_income_eq,
            [m.t, m.regions, m.quintiles],
        )
    ])
    # ============================================================================
    # DAMAGE DISTRIBUTION PER QUINTILE
    # ============================================================================

    def damage_distribution_eq(m, t, r, q):
        # calculate income_quintile^ε
        income = m.income_quintile[t, r, q]
        epsilon = m.damage_elasticity
        return income**epsilon
    
    constraints.extend([
        Equation(
            m.damage_distribution,
            damage_distribution_eq,
            [m.t, m.regions, m.quintiles],
        )
    ])

    # ============================================================================
    # SUM OF DAMAGE DISTRIBUTION (for scaling factor)
    # ============================================================================

    def sum_damage_distribution_eq(m, t, r):
        return m.sum_damage_distribution[t, r] == sum(
            m.damage_distribution[t, r, q] for q in m.quintiles
        )

    constraints.extend([
        Equation(
            m.sum_damage_distribution,
            sum_damage_distribution_eq,
            [m.t, m.regions],
        )
    ])

    # ============================================================================
    # SCALING FACTOR C: total_damage / sum(damage_distribution)
    # ============================================================================

    def damage_scaling_factor_eq(m, t, r):
        # Using total damage from COACCH component (in fraction of GDP) to calculate absolute damage
        total_damage_fraction = m.damage_costs[t, r] # fraction og GDP, from coacch.py
        total_damage_absolute = total_damage_fraction * m.GDP_net[t, r] # absolute damage in currency unit

        # Sum damage_distribution over all quintiles for a certain region and timestep
        sum_distribution = sum(m.damage_distribution[t, r, q] for q in m.quintiles)

        # C = total_damage / sum(damage_distribution)
        return total_damage_absolute / sum_distribution
    
    constraints.extend([
        Equation(
            m.damage_scaling_factor,
            damage_scaling_factor_eq,
            [m.t, m.regions],
        )
    ])
    # ============================================================================
    # ACTUAL DAMAGE PER QUINTILE: damage_quintile = C * damage_distribution
    # ============================================================================

    def damage_quintile_eq(m, t, r, q):
        return m.damage_scaling_factor[t, r] * m.damage_distribution[t, r, q]
    
    constraints.extend([
        Equation(
            m.damage_quintile,
            damage_quintile_eq,
            [m.t, m.regions, m.quintiles],
        )
    ])

    # ============================================================================
    # INCOME AFTER DAMAGES PER QUINTILE
    # ============================================================================

    def income_after_damages_eq(m, t, r, q):
        return m.income_after_damages[t, r, q] == m.income_quintile[t, r, q] - m.damage_quintile[t, r, q]
    
    constraints.extend([
        Equation(
            m.income_after_damages,
            income_after_damages_eq,
            [m.t, m.regions, m.quintiles],
        )
    ])

    # Return the list of constraints
    return constraints
