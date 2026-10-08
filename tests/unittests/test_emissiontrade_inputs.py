"""Configured payment limits in the global cost-pool component."""

import pytest
from pyomo.environ import value

from mimosa.components.emissiontrade import globalcostpool


@pytest.mark.parametrize("enabled", [False, True])
def test_costpool_initializes_payment_limits_without_full_model_assembly(
    enabled, policy_inputs, policy_model
):
    limits = {"min rel payment level": 0.2 if enabled else False,
              "max rel payment level": 1.5 if enabled else False}
    inputs = policy_inputs({"economics": {"emission trade": limits}})
    m = policy_model(inputs)
    globalcostpool.get_constraints(m, inputs)
    assert value(m.min_rel_payment_level) == limits["min rel payment level"]
    assert value(m.max_rel_payment_level) == limits["max rel payment level"]
    assert m.min_rel_payment_level.doc == "::economics.emission trade.min rel payment level"
    assert m.max_rel_payment_level.doc == "::economics.emission trade.max rel payment level"

