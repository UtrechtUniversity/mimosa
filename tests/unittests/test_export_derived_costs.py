import numpy as np
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
    model.sector_damage_costs_gross = Var(
        model.t,
        model.regions,
        units=quant.unit("fraction_of_GDP"),
        initialize={(0, "A"): 0, (0, "B"): 0, (1, "A"): 0.1, (1, "B"): 0.2},
    )
    model.sector_avoided_damages_adapt = Var(
        model.t,
        model.regions,
        units=quant.unit("fraction_of_gross_damages"),
        initialize={
            (0, "A"): 0.2,
            (0, "B"): 0.8,
            (1, "A"): 0.25,
            (1, "B"): 0.75,
        },
    )
    model.orphan_avoided_damages_adapt = Var(
        model.t,
        model.regions,
        units=quant.unit("fraction_of_gross_damages"),
        initialize=0.5,
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


def _indirect_cost_model(
    ignore_damages=False, zero_costs=False, include_adaptation=True
):
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1, 2], ordered=True)
    model.regions = Set(initialize=["A", "B"], ordered=True)
    model.year = lambda t: t
    model.period_length = Param(
        model.t, initialize={0: 0, 1: 5, 2: 10}
    )
    model.ignore_damages = Param(initialize=ignore_damages)
    model.baseline_GDP = Param(
        model.t,
        model.regions,
        initialize={
            (0, "A"): 100,
            (0, "B"): 300,
            (1, "A"): 100,
            (1, "B"): 300,
            (2, "A"): 200,
            (2, "B"): 300,
        },
        units=quant.unit("currency_unit"),
    )
    model.global_baseline_GDP = Param(
        model.t,
        initialize={0: 400, 1: 400, 2: 500},
        units=quant.unit("currency_unit"),
    )
    model.indirect_costs = Var(
        model.t,
        model.regions,
        units=quant.unit("fraction_of_baseline_GDP"),
        initialize={
            (0, "A"): 0.1,
            (0, "B"): 0.1,
            (1, "A"): 0.2,
            (1, "B"): 0.4,
            (2, "A"): 0.3,
            (2, "B"): 0.5,
        },
    )

    damage_values = {
        (0, "A"): 10,
        (0, "B"): 20,
        (1, "A"): 30,
        (1, "B"): 0,
        (2, "A"): 0,
        (2, "B"): 0,
    }
    mitigation_values = {
        (0, "A"): 30,
        (0, "B"): 20,
        (1, "A"): 10,
        (1, "B"): 0,
        (2, "A"): 0,
        (2, "B"): 0,
    }
    adaptation_values = {
        (0, "A"): 10,
        (0, "B"): 0,
        (1, "A"): 10,
        (1, "B"): 40,
        (2, "A"): 0,
        (2, "B"): 0,
    }
    if zero_costs:
        damage_values = {key: 0 for key in damage_values}
        mitigation_values = {key: 0 for key in mitigation_values}
        adaptation_values = {key: 0 for key in adaptation_values}

    cost_variables = [
        ("damage_costs_abs", damage_values),
        ("mitigation_costs_abs", mitigation_values),
    ]
    if include_adaptation:
        cost_variables.append(("adaptation_costs_abs", adaptation_values))

    for name, values in cost_variables:
        setattr(
            model,
            name,
            Var(
                model.t,
                model.regions,
                units=quant.unit("currency_unit"),
                initialize=values,
            ),
        )

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
        "global_sector_damage_costs_gross",
        "global_sector_avoided_damages_adapt",
        "global_other_costs",
        "global_heat_related_mortality",
    }
    assert rows_by_name["global_sector_damage_costs"][3:] == pytest.approx([0.1, 0.1])
    assert rows_by_name["global_sector_damage_costs_gross"][3:] == pytest.approx(
        [0, 0.16]
    )
    global_avoided = rows_by_name["global_sector_avoided_damages_adapt"][3:]
    assert np.isnan(global_avoided[0])
    assert global_avoided[1] == pytest.approx(0.625)
    assert rows_by_name["global_other_costs"][3:] == pytest.approx([0.175, 0.18])
    assert rows_by_name["global_heat_related_mortality"][3:] == pytest.approx([3, 7])


@pytest.mark.parametrize("simulation", [False, True])
def test_add_indirect_damage_cost_rows(simulation):
    model = _indirect_cost_model()

    if simulation:
        output_model = SimulationObjectModel(model)
        all_variables = output_model.all_vars_for_export()
    else:
        output_model = model
        all_variables = get_all_variables(model) + get_all_time_dependent_params(model)

    rows = []
    add_derived_global_rows(rows, output_model, all_variables)
    rows_by_name_and_region = {(row[0], row[1]): row for row in rows}

    assert rows_by_name_and_region[("indirect_damage_costs", "A")][3:] == pytest.approx(
        [0, 0.04, 0.14]
    )
    assert rows_by_name_and_region[("indirect_damage_costs", "B")][3:] == pytest.approx(
        [0, 0.2, 1 / 12]
    )
    assert rows_by_name_and_region[
        ("global_indirect_damage_costs", "Global")
    ][3:] == pytest.approx([0, 0.16, 0.106])
    assert rows_by_name_and_region[
        ("global_indirect_mitigation_costs", "Global")
    ][3:] == pytest.approx([0, 0.18, 0.09])
    assert rows_by_name_and_region[
        ("global_indirect_adaptation_costs", "Global")
    ][3:] == pytest.approx([0, 0.01, 0.224])

    for region in model.regions:
        attributed_total = np.sum(
            [
                rows_by_name_and_region[(f"indirect_{cost_type}_costs", region)][
                    3:
                ]
                for cost_type in ("damage", "mitigation", "adaptation")
            ],
            axis=0,
        )
        expected = [0] + [model.indirect_costs[t, region].value for t in (1, 2)]
        assert attributed_total == pytest.approx(expected)


@pytest.mark.parametrize("simulation", [False, True])
@pytest.mark.parametrize(
    "model_kwargs", [{"ignore_damages": True}, {"zero_costs": True}]
)
def test_indirect_damage_costs_are_zero_when_not_attributable(
    simulation, model_kwargs
):
    model = _indirect_cost_model(**model_kwargs)

    if simulation:
        output_model = SimulationObjectModel(model)
        all_variables = output_model.all_vars_for_export()
    else:
        output_model = model
        all_variables = get_all_variables(model) + get_all_time_dependent_params(model)

    rows = []
    add_derived_global_rows(rows, output_model, all_variables)

    rows_by_name_and_region = {(row[0], row[1]): row for row in rows}
    zero_cost_types = (
        ("damage", "adaptation")
        if model_kwargs.get("ignore_damages")
        else ("damage", "mitigation", "adaptation")
    )
    for cost_type in zero_cost_types:
        attributed_rows = [
            row
            for (name, _), row in rows_by_name_and_region.items()
            if name in (
                f"indirect_{cost_type}_costs",
                f"global_indirect_{cost_type}_costs",
            )
        ]
        assert len(attributed_rows) == 3
        assert all(row[3:] == [0, 0, 0] for row in attributed_rows)

    if model_kwargs.get("ignore_damages"):
        assert rows_by_name_and_region[("indirect_mitigation_costs", "A")][
            3:
        ] == pytest.approx([0, 0.2, 0.3])
        assert rows_by_name_and_region[("indirect_mitigation_costs", "B")][
            3:
        ] == pytest.approx([0, 0.4, 0.5])
        assert rows_by_name_and_region[
            ("global_indirect_mitigation_costs", "Global")
        ][3:] == pytest.approx([0, 0.35, 0.42])


@pytest.mark.parametrize("simulation", [False, True])
def test_missing_adaptation_costs_are_treated_as_zero(simulation):
    model = _indirect_cost_model(include_adaptation=False)

    if simulation:
        output_model = SimulationObjectModel(model)
        all_variables = output_model.all_vars_for_export()
    else:
        output_model = model
        all_variables = get_all_variables(model) + get_all_time_dependent_params(model)

    rows = []
    add_derived_global_rows(rows, output_model, all_variables)
    rows_by_name_and_region = {(row[0], row[1]): row for row in rows}

    for region in model.regions:
        assert rows_by_name_and_region[("indirect_adaptation_costs", region)][3:] == [
            0,
            0,
            0,
        ]
    assert rows_by_name_and_region[
        ("global_indirect_adaptation_costs", "Global")
    ][3:] == [0, 0, 0]
