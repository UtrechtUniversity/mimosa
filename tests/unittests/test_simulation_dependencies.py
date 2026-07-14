import numpy as np
import pytest
from pyomo.environ import ConcreteModel, Param, Set, Var

from mimosa.common import GlobalEquation, RegionalEquation, add_constraint
from mimosa.core.simulation import CircularDependencyError, Simulator
from mimosa.core.simulation.helpers import calc_dependencies, sort_equations


def _equation(name, dependencies=(), previous_time_dependencies=()):
    equation = GlobalEquation(name, lambda _m, _t: 0)
    # Assign instance lists explicitly so these sorting tests are independent
    # of the current class-level defaults on Equation.
    equation.dependencies = list(dependencies)
    equation.prev_time_dependencies = list(previous_time_dependencies)
    return equation


def _add_equation(model, equation):
    add_constraint(
        model,
        equation.to_pyomo_constraint(model),
        equation.name,
    )


def test_sort_equations_orders_a_linear_dependency_chain():
    """A fully ordered dependency chain should produce its single valid order."""
    equations = {
        "emissions": _equation("emissions", ["control"]),
        "cumulative_emissions": _equation(
            "cumulative_emissions", ["emissions"]
        ),
        "temperature": _equation("temperature", ["cumulative_emissions"]),
    }

    ordered, graph, controls = sort_equations(equations, return_graph=True)

    assert [equation.name for equation in ordered] == [
        "emissions",
        "cumulative_emissions",
        "temperature",
    ]
    assert controls == ["control"]
    assert graph.nodes["control"]["has_equation"] is False
    assert graph.nodes["temperature"]["has_equation"] is True


def test_sort_equations_orders_branches_before_their_merge():
    """Independent branches may vary in order, but both must precede their consumer."""
    equations = {
        "regional_emissions": _equation("regional_emissions", ["control"]),
        "mitigation_costs": _equation("mitigation_costs", ["control"]),
        "total_costs": _equation(
            "total_costs", ["regional_emissions", "mitigation_costs"]
        ),
    }

    ordered = sort_equations(equations)
    positions = {equation.name: i for i, equation in enumerate(ordered)}

    assert positions["regional_emissions"] < positions["total_costs"]
    assert positions["mitigation_costs"] < positions["total_costs"]


def test_previous_timestep_dependency_is_recorded_without_affecting_sort_order():
    """Previous-period dependencies are plotting metadata, not hard ordering edges."""
    equations = {
        "stock": _equation(
            "stock",
            dependencies=["flow"],
            previous_time_dependencies=["stock"],
        ),
        "flow": _equation("flow", dependencies=["control"]),
    }

    ordered, graph, controls = sort_equations(equations, return_graph=True)

    assert [equation.name for equation in ordered] == ["flow", "stock"]
    assert controls == ["control"]
    # The self-edge is retained in the full graph for plotting, but it is not
    # part of the hard-dependency graph used to order simulation equations.
    assert graph.edges["stock", "stock"]["type"] == "prev_time_dependency"


def test_sort_equations_reports_same_timestep_cycles():
    """Mutually dependent equations in one period cannot be simulated sequentially."""
    equations = {
        "a": _equation("a", ["c"]),
        "b": _equation("b", ["a"]),
        "c": _equation("c", ["b"]),
    }

    with pytest.raises(CircularDependencyError) as exc_info:
        sort_equations(equations)

    message = str(exc_info.value)
    assert "Circular dependencies found" in message
    assert all(name in message for name in ["a", "b", "c"])


def test_sort_equations_detects_multiple_control_variables():
    equations = {
        "output": _equation("output", ["control_a", "control_b"]),
    }

    ordered, _graph, controls = sort_equations(equations, return_graph=True)

    assert [equation.name for equation in ordered] == ["output"]
    assert set(controls) == {"control_a", "control_b"}


@pytest.mark.xfail(
    strict=True,
    reason="sort_equations currently omits equation nodes without graph edges",
)
def test_sort_equations_keeps_an_equation_without_dependencies():
    equations = {"constant": _equation("constant")}

    ordered = sort_equations(equations)

    assert [equation.name for equation in ordered] == ["constant"]


def test_calc_dependencies_detects_variables_and_excludes_parameters():
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1, 2], ordered=True)
    model.input = Var(model.t, initialize=0)
    model.factor = Param(initialize=3.0)
    model.output = Var(model.t, initialize=0)
    equation = GlobalEquation(
        model.output,
        lambda m, t: m.input[t] * m.factor,
    )
    _add_equation(model, equation)

    calc_dependencies({equation.name: equation}, model)

    assert set(equation.dependencies) == {"input"}
    assert equation.prev_time_dependencies == []


def test_calc_dependencies_detects_global_and_regional_variables():
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1, 2], ordered=True)
    model.regions = Set(initialize=["A", "B"], ordered=True)
    model.regional_input = Var(model.t, model.regions, initialize=0)
    model.global_input = Var(model.t, initialize=0)
    model.regional_factor = Param(
        model.t, model.regions, initialize=lambda _m, _t, _r: 2.0
    )
    model.output = Var(model.t, model.regions, initialize=0)
    equation = RegionalEquation(
        model.output,
        lambda m, t, r: (
            m.regional_input[t, r]
            + m.global_input[t] * m.regional_factor[t, r]
        ),
    )
    _add_equation(model, equation)

    calc_dependencies({equation.name: equation}, model)

    assert set(equation.dependencies) == {"regional_input", "global_input"}
    assert equation.prev_time_dependencies == []


def test_calc_dependencies_distinguishes_previous_timestep_variables():
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1, 2], ordered=True)
    model.flow = Var(model.t, initialize=0)
    model.stock = Var(model.t, initialize=0)
    equation = GlobalEquation(
        model.stock,
        lambda m, t: m.stock[t - 1] + m.flow[t] if t > 0 else 0,
    )
    _add_equation(model, equation)

    calc_dependencies({equation.name: equation}, model)

    assert set(equation.dependencies) == {"flow"}
    assert set(equation.prev_time_dependencies) == {"stock"}


@pytest.mark.xfail(
    strict=True,
    reason="calc_dependencies currently assumes a timestep labelled 1 exists",
)
def test_calc_dependencies_supports_year_labels():
    model = ConcreteModel()
    model.t = Set(initialize=[2020, 2025, 2030], ordered=True)
    model.input = Var(model.t, initialize=0)
    model.output = Var(model.t, initialize=0)
    equation = GlobalEquation(model.output, lambda m, t: 2 * m.input[t])
    _add_equation(model, equation)

    calc_dependencies({equation.name: equation}, model)

    assert set(equation.dependencies) == {"input"}


@pytest.mark.xfail(
    strict=True,
    reason="prepare_simulation currently overwrites duplicate equation names",
)
def test_prepare_simulation_rejects_duplicate_equation_lhs(monkeypatch):
    first = _equation("output", ["first_control"])
    second = _equation("output", ["second_control"])
    simulator = Simulator()

    monkeypatch.setattr(
        "mimosa.core.simulation.simulator.calc_dependencies",
        lambda _equations, _model: None,
    )

    with pytest.raises(ValueError, match="Duplicate equation"):
        simulator.prepare_simulation([first, second], object())


def test_prepare_and_run_minimal_simulation_model():
    """Equation conversion, dependency sorting, and simulation should work together."""
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1, 2], ordered=True)
    model.year = lambda t: 2020 + 5 * t
    model.control = Var(model.t, initialize=0)
    model.flow = Var(model.t, initialize=0)
    model.stock = Var(model.t, initialize=0)

    equations = [
        GlobalEquation(model.flow, lambda m, t: 2 * m.control[t]),
        GlobalEquation(
            model.stock,
            lambda m, t: m.stock[t - 1] + m.flow[t] if t > 0 else 0,
        ),
    ]
    for equation in equations:
        _add_equation(model, equation)

    simulator = Simulator()
    simulator.prepare_simulation(equations, model)
    result = simulator.run(control=np.array([1.0, 2.0, 3.0]))

    np.testing.assert_allclose(result.flow.values, [2.0, 4.0, 6.0])
    np.testing.assert_allclose(result.stock.values, [0.0, 4.0, 10.0])
