import pytest
from tests.modeltests.utils import exec_run, SolverStatus, read_output

pytestmark = pytest.mark.ipopt


@pytest.fixture(scope="module")
def script_output():
    """Runs the script shown in the documentation"""
    return exec_run("runs/run_effortsharing.py")


def test_run_successfully(script_output):
    """Last run should be successful"""
    assert script_output["model1"].status == SolverStatus.ok


def test_equal_mitigation_costs(script_output):
    """
    Effort-sharing regime: equal_mitigation_costs

    Check if mitigation costs are equal for all regions
    """
    output_df_ind = read_output(filename="run_equal_mitigation_costs")

    mitigation_costs = output_df_ind.loc["rel_mitigation_costs", "2025":]

    relative_standard_deviation = mitigation_costs.std() / mitigation_costs.mean()

    # Check if relative standard deviation is below 1%
    assert relative_standard_deviation.max() < 0.01


def test_equal_total_costs(script_output):
    """
    Effort-sharing regime: equal_total_costs

    Check if mitigation plus damage costs (plus optional financial transfers)
    are equal for all regions
    """
    output_df_ind = read_output(filename="run_equal_total_costs")

    total_costs = (
        output_df_ind.loc["rel_mitigation_costs", "2025":]
        + output_df_ind.loc["damage_costs", "2025":]
        + output_df_ind.loc["rel_financial_transfer", "2025":]
    )

    relative_standard_deviation = total_costs.std() / total_costs.mean()

    # Check if relative standard deviation is below 1%
    assert relative_standard_deviation.max() < 0.01


def test_per_cap_convergence(script_output):
    """
    Effort-sharing regime: per_cap_convergence

    Check if emissions per capita are equal after convergence year (2050)
    Note that the emissions are after emission trade, so they are not equal
    to the direct variable regional_emissions.
    """
    output_df_ind = read_output(filename="run_per_cap_convergence").loc[:, "2020":]

    per_capita_emissions = (
        output_df_ind.loc["regional_emission_allowances"]
        / output_df_ind.loc["population"]
    )
    per_capita_emissions_deviation = per_capita_emissions.std()

    # Before 2050, emissions per capita are not equal (larger than 0.5 GtCO2 per capita deviation):
    assert per_capita_emissions_deviation["2030"] > 0.5

    # After 2050, emissions per capita are equal (smaller than 0.05 GtCO2 per capita deviation):
    assert per_capita_emissions_deviation["2050":].max() < 0.05

    # Check that regional emission allowances are equal to baseline emissions minus paid for emission reductions
    # (emissions after trade)
    allowances_diff = output_df_ind.loc["regional_emission_allowances"] - (
        output_df_ind.loc["baseline"]
        - output_df_ind.loc["paid_for_emission_reductions"]
    )
    assert allowances_diff.max().max() < 0.001
