import pytest
from pyomo.environ import ConcreteModel, Param, Set, Var

from mimosa.common import get_all_time_dependent_params, get_all_variables, quant
from mimosa.core.simulation import SimulationObjectModel
from mimosa.export.save import add_derived_global_rows


def _cost_model():
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1], ordered=True)
    model.regions = Set(initialize=["A", "B"], ordered=True)
    model.year = lambda t: t

    model.GDP_gross = Var(
        model.t,
        model.regions,
        initialize={(0, "A"): 100, (0, "B"): 300, (1, "A"): 200, (1, "B"): 300},
    )
    model.global_GDP_gross = Var(model.t, initialize={0: 400, 1: 500})
    model.sector_damage_costs = Var(
        model.t,
        model.regions,
        units=quant.unit("fraction_of_GDP"),
        initialize={(0, "A"): 0.1, (0, "B"): 0.2, (1, "A"): 0.3, (1, "B"): 0.1},
    )
    model.sector_damage_costs_abs = Var(
        model.t,
        model.regions,
        units=quant.unit("currency_unit"),
        initialize={(0, "A"): 10, (0, "B"): 30, (1, "A"): 20, (1, "B"): 30},
    )
    model.other_costs = Var(
        model.t,
        model.regions,
        units=quant.unit("fraction_of_GDP"),
        initialize={(0, "A"): 0.1, (0, "B"): 0.2, (1, "A"): 0.3, (1, "B"): 0.1},
    )
    model.existing_costs = Var(
        model.t,
        model.regions,
        units=quant.unit("fraction_of_GDP"),
        initialize=0.2,
    )
    model.global_existing_costs = Var(
        model.t, units=quant.unit("fraction_of_GDP"), initialize=0.5
    )
    model.reference_costs = Param(
        model.t,
        model.regions,
        units=quant.unit("fraction_of_GDP"),
        initialize=0.4,
    )
    model.indirect_costs = Var(
        model.t,
        model.regions,
        units=quant.unit("fraction_of_baseline_GDP"),
        initialize=0.3,
    )
    model.financial_transfer = Var(
        model.t,
        model.regions,
        units=quant.unit("fraction_of_GDP"),
        initialize=0.1,
    )
    model.heat_related_mortality = Var(
        model.t,
        model.regions,
        units=quant.unit("billion people"),
        initialize={(0, "A"): 1, (0, "B"): 2, (1, "A"): 3, (1, "B"): 4},
    )
    model.existing_population_quantity = Var(
        model.t,
        model.regions,
        units=quant.unit("million people"),
        initialize=2,
    )
    model.global_existing_population_quantity = Var(
        model.t,
        units=quant.unit("million people"),
        initialize=4,
    )
    model.reference_population_quantity = Param(
        model.t,
        model.regions,
        units=quant.unit("billion people"),
        initialize=5,
    )
    model.population_rate = Var(
        model.t,
        model.regions,
        units=quant.unit("million people / year"),
        initialize=6,
    )
    model.unitless_metric = Var(model.t, model.regions, initialize=7)
    return model


@pytest.mark.parametrize("simulation", [False, True])
def test_add_derived_global_rows(simulation):
    model = _cost_model()

    if simulation:
        output_model = SimulationObjectModel(model)
        all_variables = output_model.all_vars_for_export()
    else:
        output_model = model
        all_variables = get_all_variables(model) + get_all_time_dependent_params(model)

    rows = []
    add_derived_global_rows(rows, output_model, all_variables)

    rows_by_name = {row[0]: row for row in rows}
    assert set(rows_by_name) == {
        "global_sector_damage_costs",
        "global_other_costs",
        "global_heat_related_mortality",
    }
    assert rows_by_name["global_sector_damage_costs"][3:] == pytest.approx([0.1, 0.1])
    assert rows_by_name["global_other_costs"][3:] == pytest.approx([0.175, 0.18])
    assert rows_by_name["global_heat_related_mortality"][3:] == pytest.approx([3, 7])
