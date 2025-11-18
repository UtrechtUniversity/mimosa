import pytest

from mimosa.common import (
    ConcreteModel,
    Var,
    Set,
    RegionalEquation,
    GlobalEquation,
    add_constraint,
)
from mimosa.core.simulation import Simulator, CircularDependencyError


def create_m():
    m = ConcreteModel()
    m.t = Set(initialize=[0, 1, 2, 3])
    m.regions = Set(initialize=["region1", "region2"])
    m.var1 = Var(m.t)
    m.var2 = Var(m.t)
    m.var3 = Var(m.t, m.regions)
    return m


@pytest.fixture
def m1():
    return create_m()


@pytest.fixture
def equations1(m1):

    m = m1

    equations = [
        RegionalEquation(m.var3, lambda m, t, r: m.var2[t] + 5),
        GlobalEquation(m.var2, lambda m, t: m.var1[t] ** 2 + 1),
    ]

    for eq in equations:
        add_constraint(m, eq.to_pyomo_constraint(m), eq.name)

    return equations


def test_dependencies1(m1, equations1):
    """
    With the set of equations1, there are no circular dependencies.
    This test checks that the dependencies are calculated correctly.
    The equation for var2 depends on var1, and the equation for var3 depends on var2.
    They should be ordered accordingly: first var2, then var3.
    """
    simulator = Simulator()
    simulator.prepare_simulation(equations1, m1)

    equations_dict = {eq.name: eq for eq in equations1}
    assert equations_dict["var2"].dependencies == ["var1"]
    assert equations_dict["var3"].dependencies == ["var2"]

    # First sorted equation should be var2, then var3
    assert simulator.equations_sorted[0].name == "var2"
    assert simulator.equations_sorted[1].name == "var3"


@pytest.fixture
def m2():
    return create_m()


@pytest.fixture
def equations2(m2):

    m = m2

    equations = [
        # Create a circular dependency
        RegionalEquation(m.var3, lambda m, t, r: m.var2[t] + 5),
        GlobalEquation(
            m.var2, lambda m, t: m.var1[t] + sum(m.var3[t, r] for r in m.regions)
        ),
    ]

    for eq in equations:
        add_constraint(m, eq.to_pyomo_constraint(m), eq.name)

    return equations


def test_dependencies2(m2, equations2):
    """
    With equations2, there is a circular dependency between var2 and var3.
    This test checks that the CircularDependencyError is raised.
    """
    simulator = Simulator()
    with pytest.raises(CircularDependencyError):
        simulator.prepare_simulation(equations2, m2)
