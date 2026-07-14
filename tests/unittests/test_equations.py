from types import SimpleNamespace

import pytest
from pyomo.environ import ConcreteModel, Constraint, Param, Set, Var, value

from mimosa.common import Equation, GlobalEquation, RegionalEquation


def test_global_equation_evaluates_rhs_without_pyomo():
    model = SimpleNamespace(input={0: 2.0, 1: 3.0}, factor=4.0)
    equation = GlobalEquation(
        "output",
        lambda m, t: m.input[t] * m.factor,
    )

    assert equation(model, 1) == 12.0
    assert equation.lhs == "output"
    assert equation.name == "output"
    assert equation.indices == ["t"]


def test_regional_equation_evaluates_rhs_without_pyomo():
    model = SimpleNamespace(
        input={(0, "A"): 2.0, (0, "B"): 5.0},
        offset={"A": 1.0, "B": 3.0},
    )
    equation = RegionalEquation(
        "output",
        lambda m, t, r: m.input[t, r] + m.offset[r],
    )

    assert equation(model, 0, "B") == 8.0
    assert equation.indices == ["t", "regions"]


def test_global_equation_converts_to_pyomo_constraint():
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1], ordered=True)
    model.input = Param(model.t, initialize={0: 2.0, 1: 3.0})
    model.output = Var(model.t)

    equation = GlobalEquation(
        model.output,
        lambda m, t: 2 * m.input[t],
    )
    model.constraint_output = equation.to_pyomo_constraint(model)
    model.output[1].set_value(6.0)

    assert equation.lhs == "output"
    constraint = model.constraint_output[1]
    assert value(constraint.body) == pytest.approx(value(constraint.lower))


def test_regional_equation_converts_to_pyomo_constraint():
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1], ordered=True)
    model.regions = Set(initialize=["A", "B"], ordered=True)
    model.input = Param(
        model.t,
        model.regions,
        initialize=lambda _m, t, r: t + (1 if r == "A" else 2),
    )
    model.output = Var(model.t, model.regions)

    equation = RegionalEquation(
        model.output,
        lambda m, t, r: 3 * m.input[t, r],
    )
    model.constraint_output = equation.to_pyomo_constraint(model)
    model.output[1, "B"].set_value(9.0)

    constraint = model.constraint_output[1, "B"]
    assert value(constraint.body) == pytest.approx(value(constraint.lower))


def test_general_equation_supports_three_indices():
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1], ordered=True)
    model.regions = Set(initialize=["A", "B"], ordered=True)
    model.scenarios = Set(initialize=["low", "high"], ordered=True)
    model.output = Var(model.t, model.regions, model.scenarios)

    equation = Equation(
        model.output,
        lambda _m, t, r, scenario: t
        + (1 if r == "B" else 0)
        + (2 if scenario == "high" else 0),
        indices=[model.t, model.regions, model.scenarios],
    )
    model.constraint_output = equation.to_pyomo_constraint(model)
    model.output[1, "B", "high"].set_value(4.0)

    assert equation.indices == ["t", "regions", "scenarios"]
    constraint = model.constraint_output[1, "B", "high"]
    assert value(constraint.body) == pytest.approx(value(constraint.lower))


def test_equation_skip_semantics_for_pyomo_and_simulation():
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1], ordered=True)
    model.output = Var(model.t)

    equation = GlobalEquation(
        model.output,
        lambda _m, t: Constraint.Skip if t == 0 else 5.0,
    )
    model.constraint_output = equation.to_pyomo_constraint(model)

    assert 0 not in model.constraint_output
    assert 1 in model.constraint_output
    # This records the current simulation convention. A skipped equation is
    # currently represented as zero in simulation mode.
    assert equation(model, 0) == 0
