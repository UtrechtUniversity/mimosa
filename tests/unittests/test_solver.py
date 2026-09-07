from pyomo.environ import ConcreteModel, Constraint, Objective, Var

from mimosa.core.solver import _deactivate_trivial_constraints_if_required


def test_trivial_constraints_remain_active_with_sufficient_degrees_of_freedom():
    model = ConcreteModel()
    model.x = Var(initialize=1)
    model.constraint = Constraint(expr=model.x == 1)
    model.objective = Objective(expr=model.x)

    _deactivate_trivial_constraints_if_required(model)

    assert model.constraint.active


def test_trivial_constraints_are_deactivated_if_equalities_outnumber_variables():
    model = ConcreteModel()
    model.x = Var(initialize=1)
    model.x.fix()
    model.constraint = Constraint(expr=model.x == 1)

    _deactivate_trivial_constraints_if_required(model)

    assert not model.constraint.active
