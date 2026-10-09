from mimosa.base_model import create_base_model
from mimosa.common import ConcreteModel, PyomoParam, quant, value
from mimosa.common.config.parseconfig import check_params, parse_param_values
from mimosa.common.data import DataStore
from mimosa.common.regional_params import RegionalParamStore
from mimosa.core.model_inputs import ModelInputs
import pytest


@pytest.mark.parametrize("settings,years", [
    ({"time": {"end": 2040, "periods": {2030: 10}},
      "regions": {"USA": {"economics": {"gdp_ppp_2010_div_gdp_mer_2010": 2.5}}, "CAN": {}}},
     [2025, 2030, 2040]),
    ({"time": {"end": 2035, "dt": 2.5, "periods": {}}, "regions": {"CAN": {}}},
     [2025, 2027.5, 2030, 2032.5, 2035]),
])
def test_create_base_model_defines_shared_sets_and_inputs(settings, years):
    """The extracted base model must retain every shared model declaration."""
    params, tree = check_params(settings, return_parser_tree=True)
    params = parse_param_values(params)
    inputs = ModelInputs(params, tree, DataStore(params), RegionalParamStore(params, tree))
    model = create_base_model(inputs)

    assert model.regions.isordered()
    for name in (
        "beginyear",
        "tf",
        "t",
        "period_length",
        "year",
        "regions",
        "population",
        "global_population",
        "baseline_GDP",
        "global_baseline_GDP",
        "gdp_ppp_2010_div_gdp_mer_2010",
        "dollar_2017_MER_to_2010_PPP",
        "ssp_baseline_emissions",
    ):
        assert hasattr(model, name)
    assert not hasattr(model, "MAC_SSP_calibration_factor")
    assert isinstance(model, ConcreteModel)
    assert all(parameter.is_constructed() for parameter in model.component_objects(PyomoParam))
    assert tuple(model.regions) == tuple(settings["regions"])
    assert [model.year(t) for t in model.t] == years
    assert value(model.tf) == len(years) - 1
    assert [value(model.period_length[t]) for t in model.t] == [0] + [b - a for a, b in zip(years, years[1:])]
    assert model.beginyear.doc == "::time.start"
    assert model.population.doc == "timeandregional::population"
    assert str(model.population.get_units()) == str(quant.unit("billion people"))
    for t in model.t:
        assert value(model.global_population[t]) == pytest.approx(sum(value(model.population[t, r]) for r in model.regions))
        assert value(model.global_baseline_GDP[t]) == pytest.approx(sum(value(model.baseline_GDP[t, r]) for r in model.regions))
        for r in model.regions:
            assert value(model.baseline_GDP[t, r]) == pytest.approx(inputs.data_store.interp_data(model.year(t), r, "GDP"))
            assert value(model.ssp_baseline_emissions[t, r]) == pytest.approx(inputs.data_store.interp_data(model.year(t), r, "emissions"))
    if "USA" in model.regions:
        assert value(model.dollar_2017_MER_to_2010_PPP["USA"]) == pytest.approx(0.89632 * 2.5)
