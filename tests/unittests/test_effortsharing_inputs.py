"""Configured convergence, historical emissions debt and discrete repayment."""

import numpy as np
import pandas as pd
import pytest
from pyomo.environ import value

from mimosa.components.effortsharing import equal_cumulative_per_cap, per_cap_convergence


@pytest.mark.parametrize("year", [2025, 2035])
def test_convergence_uses_configured_year_for_derived_shares(
    year, policy_inputs, policy_model
):
    inputs = policy_inputs({"effort sharing": {"percapconv_year": year}})
    m = policy_model(inputs)
    per_cap_convergence.get_constraints(m, inputs)
    assert value(m.percapconv_year) == year
    assert m.percapconv_year.doc == "::effort sharing.percapconv_year"
    for t in m.t:
        weight = 1 if year == 2025 else min((m.year(t) - 2025) / (year - 2025), 1)
        for region, initial_share in (("USA", 0.8), ("CAN", 0.2)):
            population_share = value(m.population[t, region]) / value(m.global_population[t])
            expected = weight * population_share + (1 - weight) * initial_share
            assert value(m.percapconv_share[t, region]) == pytest.approx(expected)


@pytest.mark.parametrize("end_year", [2045, False])
def test_ecpc_nondefault_inputs_preserve_debt_and_discrete_repayment(
    monkeypatch, end_year, policy_inputs, policy_model
):
    years = [2010, 2015, 2020]
    emissions = pd.DataFrame({"USA": [8, 12, 15], "CAN": [2, 3, 5]}, index=years)
    population = pd.DataFrame({"USA": [2, 3, 4], "CAN": [1, 1, 1]}, index=years)
    monkeypatch.setattr(equal_cumulative_per_cap, "_load_data", lambda: (emissions, population))
    inputs = policy_inputs({"effort sharing": {"ecpc_repayment_endyear": end_year}})
    m = policy_model(inputs)
    equal_cumulative_per_cap.get_constraints(m, inputs)
    assert value(m.effortsharing_ecpc_discount_rate) == 0.05
    assert value(m.effortsharing_ecpc_start_year) == 2010
    assert value(m.effortsharing_ecpc_repayment_endyear) == end_year
    for name, path in (("discount_rate", "ecpc_discount_rate"), ("start_year", "ecpc_start_year"),
                       ("repayment_endyear", "ecpc_repayment_endyear")):
        assert getattr(m, "effortsharing_ecpc_" + name).doc == "::effort sharing." + path
    for region in m.regions:
        fair_share = population[region].to_numpy() / population.sum(axis=1).to_numpy() * emissions.sum(axis=1).to_numpy()
        debt = float(np.sum((emissions[region].to_numpy() - fair_share) * np.exp(-0.05 * (2025 - np.array(years)))))
        assert abs(debt) > 0
        assert value(m.effortsharing_ecpc_historical_debt[0, region]) == pytest.approx(debt)
        repayments = [value(m.effortsharing_ecpc_annual_debt_repayment[t, region]) for t in m.t]
        assert sum(repayments[t] * value(m.period_length[t]) for t in m.t) == pytest.approx(debt)
        if end_year is False:
            assert repayments == pytest.approx([debt / 25] * len(m.t))
        else:
            assert repayments[-1] == 0

