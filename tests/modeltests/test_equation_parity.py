import itertools

import pytest
from pyomo.environ import value

from mimosa import MIMOSA, load_params


pytestmark = pytest.mark.simulation


@pytest.fixture(scope="module")
def model_states():
    """Create equivalent, nontrivial simulation and Pyomo model states."""
    model = MIMOSA(load_params(), prerun=False)
    simulation_model = model.run_simulation(relative_abatement=0.2)
    model.simulator.initialize_pyomo_model(
        model.concrete_model,
        simulation_model,
    )
    return model, simulation_model


def test_all_equations_match_between_pyomo_and_simulation(model_states):
    """Every equation RHS should agree in Pyomo and simulation execution modes."""
    model, simulation_model = model_states
    comparisons = 0

    for equation in model.equations:
        index_values = [
            getattr(simulation_model, index_name)
            for index_name in equation.indices
        ]

        for indices in itertools.product(*index_values):
            pyomo_result = value(equation(model.concrete_model, *indices))
            simulation_result = equation(simulation_model, *indices)

            assert simulation_result == pytest.approx(
                pyomo_result,
                rel=1e-10,
                abs=1e-10,
                nan_ok=True,
            ), f"Equation {equation.name} differs at index {indices}"
            comparisons += 1

    assert comparisons > 0


def test_pyomo_and_simulation_share_the_varying_time_grid(model_states):
    model, simulation_model = model_states
    pyomo_model = model.concrete_model

    expected_years = [
        2025,
        2030,
        2035,
        2040,
        2045,
        2050,
        2060,
        2070,
        2080,
        2090,
        2100,
        2110,
        2120,
        2130,
        2140,
        2150,
    ]
    assert [pyomo_model.year(t) for t in pyomo_model.t] == expected_years
    assert [value(pyomo_model.period_length[t]) for t in pyomo_model.t] == [
        0,
        *([5] * 5),
        *([10] * 10),
    ]
    assert simulation_model.period_length.values.tolist() == [
        0,
        *([5] * 5),
        *([10] * 10),
    ]
