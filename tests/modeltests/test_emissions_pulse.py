import pytest
from pyomo.environ import value

from mimosa import MIMOSA, load_params

pytestmark = pytest.mark.simulation


def run_nopolicy(pulse_amount="0 GtCO2", pulse_year=2030):
    params = load_params()
    params["emissions"]["baseline carbon intensity"] = False
    params["emissions"]["pulse"]["year"] = pulse_year
    params["emissions"]["pulse"]["amount"] = pulse_amount
    model = MIMOSA(params, prerun=False)
    return model, model.run_simulation()


def test_pulse_is_added_once_to_cumulative_emissions():
    _, no_pulse = run_nopolicy()
    model, with_pulse = run_nopolicy("1 GtCO2")

    for t in with_pulse.t:
        expected_difference = 1.0 if with_pulse.year(t) >= 2030 else 0.0
        assert (
            with_pulse.global_cumulative_emissions[t]
            - no_pulse.global_cumulative_emissions[t]
        ) == pytest.approx(expected_difference)

        expected_temperature_difference = (
            value(model.concrete_model.TCRE) * expected_difference
        )
        assert with_pulse.temperature[t] - no_pulse.temperature[t] == pytest.approx(
            expected_temperature_difference
        )


def test_pulse_does_not_change_emissions_or_mitigation_costs():
    _, no_pulse = run_nopolicy()
    _, with_pulse = run_nopolicy("1 GtCO2")

    for t in with_pulse.t:
        assert with_pulse.global_emissions[t] == pytest.approx(
            no_pulse.global_emissions[t]
        )
        for region in with_pulse.regions:
            assert with_pulse.mitigation_costs_abs[t, region] == pytest.approx(
                no_pulse.mitigation_costs_abs[t, region]
            )


def test_pulse_amount_is_converted_to_model_units():
    model, _ = run_nopolicy("1000 MtCO2")

    assert value(model.concrete_model.emissions_pulse_amount) == pytest.approx(1.0)


def test_nonzero_pulse_year_must_be_on_time_grid():
    with pytest.raises(
        ValueError, match="pulse year 2032 is not on the model time grid"
    ):
        run_nopolicy("1 GtCO2", pulse_year=2032)
