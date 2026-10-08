"""Objective input metadata, discounting and optimisation direction."""

from math import exp

import pytest
from pyomo.environ import maximize, minimize, value

from mimosa.common import Param
from mimosa.components.objective import globalcosts, utility


@pytest.mark.parametrize("component", [utility, globalcosts])
def test_objectives_initialize_prtp_and_preserve_discounting(
    component, policy_inputs, policy_model
):
    inputs = policy_inputs()
    m = policy_model(inputs)
    m.global_welfare = Param(m.t, initialize=100)
    objective, constraints = component.get_constraints(m, inputs)
    m.objective = objective
    if component is globalcosts:
        m.cost_recurrence = constraints[0].to_pyomo_constraint(m)
    for t in m.t:
        m.NPV[t].set_value(10 * t)
    assert value(m.PRTP) == 0.02
    assert m.PRTP.doc == "::economics.PRTP"
    assert value(m.objective) == 30
    if component is utility:
        assert m.objective.sense == maximize
        assert value(constraints[0](m, 1)) == pytest.approx(5 * exp(-0.02 * 5) * 100)
    else:
        assert m.objective.sense == minimize
        cost = 2 * (5 + (0.02 + 0.005) * 100)
        assert value(m.cost_recurrence[1].body) == pytest.approx(10 - 5 * exp(-0.02 * 5) * cost)

